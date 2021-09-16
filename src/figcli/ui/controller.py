import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Any

import botocore
from botocore.exceptions import ClientError
from figgy.utils.exceptions import FiggyValidationError
from flask import Response, request
from pydantic import BaseModel

from figcli.commands.command_context import CommandContext
from figcli.models.assumable_role import AssumableRole
from figcli.svcs.audit import AuditService
from figcli.svcs.one_time_secret import OTSService
from figcli.svcs.service_registry import ServiceRegistry
from figcli.svcs.usage_tracking import UsageTrackingService
from figcli.ui.exceptions import CannotRetrieveMFAException, InvalidCredentialsException, BadRequestParameters
from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.ui.route import Route
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


class ResponseBuilder:
    @staticmethod
    def build(response: FiggyResponse) -> Response:
        log.info(f"Setting status code of: {response.status_code}")
        resp = Response(response.json(), content_type=Controller.JSON_CONTENT_TYPE)
        resp.status_code = response.status_code
        return resp


class Controller:
    JSON_CONTENT_TYPE = 'application/json; charset=utf-8'

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        self.prefix = prefix
        self._routes: List[Route] = []
        self._registry = svc_registry
        self.context = context

    def _cfg(self, refresh: bool = False, env: GlobalEnvironment = None):
        if not env:
            env = self.get_environment()

        return self._registry.config_svc(env, refresh)

    def _cfg_view(self, refresh: bool = False) -> RBACLimitedConfigView:
        return self._registry.rbac_view(self.get_environment(), refresh)

    def _audit(self, refresh: bool = False) -> AuditService:
        return self._registry.audit_svc(self.get_environment(), refresh)

    def _usage(self, refresh: bool = False) -> UsageTrackingService:
        return self._registry.usage_svc(self.get_environment(), refresh)

    def _ots(self, refresh: bool = False) -> OTSService:
        return self._registry.ots_svc(self.get_environment(), refresh)

    def routes(self) -> List[Route]:
        return self._routes

    def get_environment(self) -> GlobalEnvironment:
        # return self.context.defaults.assumable_roles[0]
        return GlobalEnvironment(
            role=AssumableRole(**json.loads(request.headers.get('ActiveRole'))),
            region=request.headers.get('ActiveRegion'))

    # Todo validate all params before throwing exception
    def get_param(self, name: str, required=True, default: any = None):
        param = request.args.get(name)

        if (required and not default) and (not param or param == 'null' or param == 'undefined'):
            raise BadRequestParameters(f'Expected query parameter missing: {name}, got value: {param}', [name])

        # Return parameter if it's set, else default. Passed in strings of 'null' or 'undefined' count as not set.
        return param if (param and param != 'null' and param != 'undefined') else default

    @staticmethod
    def to_json(obj: Any):
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, BaseModel):
            return obj.json()
        else:
            return json.dumps(obj)

    @staticmethod
    def return_json(func) -> any:
        """
        Converts the response to JSON unless it's a string, then we just return the string.
        """

        def wrapper(*args, **kwargs):
            return Controller.to_json(func(*args, **kwargs))

        return wrapper

    @staticmethod
    def client_cache(seconds=15, content_type=JSON_CONTENT_TYPE):
        """ Flask decorator that allow to set Expire and Cache headers. """

        def fwrap(f):
            @wraps(f)
            def wrapped_f(*args, **kwargs):
                result = f(*args, **kwargs)
                if isinstance(result, Response):
                    rsp = result
                else:
                    result = Controller.to_json(result)
                    rsp = Response(result, content_type=content_type)

                then = datetime.now() + timedelta(seconds=seconds)
                rsp.headers.add('Expires', then.strftime("%a, %d %b %Y %H:%M:%S GMT"))
                rsp.headers.add('Cache-Control', 'public,max-age=%d' % int(seconds))
                return rsp

            return wrapped_f

        return fwrap

    @staticmethod
    def handle_result(result):
        if result is None:
            result = {}

        if isinstance(result, FiggyResponse):
            return Response(result.json(), content_type=Controller.JSON_CONTENT_TYPE)

        response = Response(FiggyResponse(data=result).json(), content_type=Controller.JSON_CONTENT_TYPE)
        # log.info(f"RETURNING RESPONSE: {response.data}")
        return response

    @staticmethod
    def build_response(method):
        """Builds a FiggyResponse from the current return type"""

        @wraps(method)
        def impl(self, *args, **kwargs):
            try:
                result = method(self, *args, **kwargs)
                return Controller.handle_result(result)
            except ClientError as e:
                log.warning(e)
                # If we get a AccessDenied exception to decrypt this parameter, it must be encrypted
                if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                    return ResponseBuilder.build(FiggyResponse.no_decrypt_access())
                elif "AccessDeniedException" == e.response['Error']['Code']:
                    return ResponseBuilder.build(FiggyResponse.no_access_to_parameter())
                elif "ParameterNotFound" == e.response['Error']['Code']:
                    return ResponseBuilder.build(FiggyResponse.fig_missing())
                elif "ExpiredTokenException" == e.response['Error']['Code']:
                    try:
                        log.warning(f'Found expired session, triggering rerunning function with refresh=True')
                        result = method(self, *args, **kwargs, refresh=True)
                        return Controller.handle_result(result)
                    except ClientError as e3:
                        if "ExpiredTokenException" == e3.response['Error']['Code']:
                            if self.context.defaults.mfa_enabled:
                                log.info("Caught EXPIRED TOKEN TWICE! We might need MFA")
                                return ResponseBuilder.build(FiggyResponse.mfa_required())
                            else:
                                log.info("Expired TOKEN TWICE (but also we don't need MFA) - this is perplexing...")
                                return ResponseBuilder.build(FiggyResponse.force_reauth())
                        else:
                            log.error("Failed to reauth after catching ExpiredTokenException.")
                            log.exception(e3)

            except botocore.exceptions.ParamValidationError as e2:
                log.warning(f'Caught parameter validation exception: ${e2}')
                log.warning(e2)
                return ResponseBuilder.build(FiggyResponse.fig_invalid())
            except CannotRetrieveMFAException as e4:
                log.info(f"MFA auth is required. Notifying UI of expired session.")
                log.warning(e4)
                return ResponseBuilder.build(FiggyResponse.mfa_required())
            except InvalidCredentialsException as e5:
                log.info(f"Invalid credentials provided!")
                return ResponseBuilder.build(FiggyResponse.force_reauth())
            except BadRequestParameters as e6:
                log.warning(e6)
                log.info(f"Got request with invalid parameters: {e6.invalid_parameters}")
                return ResponseBuilder.build(FiggyResponse.invalid_parameters(e6.invalid_parameters))
            except ValueError as e7:
                log.warning(f"Validation error caught: {e7}")
                return ResponseBuilder.build(FiggyResponse.validation_error(f'{e7}'))
            except FiggyValidationError as e8:
                log.warning(f"Validation error caught: {e8.message}")
                return ResponseBuilder.build(FiggyResponse.validation_error(f'{e8.message}'))
            except BaseException as e1:
                log.warning(f'Caught unexpected exception: {e1}')
                log.exception(e1)

        return impl
