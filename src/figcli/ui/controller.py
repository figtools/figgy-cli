import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Any

import botocore
from botocore.exceptions import ClientError
from flask import Response, request
from pydantic import BaseModel

from figcli.models.assumable_role import AssumableRole
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.route import Route
from figcli.utils.utils import Utils
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

    def __init__(self, prefix: str, svc_registry: ServiceRegistry):
        self.prefix = prefix
        self._routes: List[Route] = []
        self._registry = svc_registry

    def _cfg(self):
        return self._registry.config_svc(self.get_role())
        # return self.registry.config_svc(self.context.defaults.assumable_roles[0])

    def _cfg_view(self) -> RBACLimitedConfigView:
        return self._registry.rbac_view(self.get_role())

    def routes(self) -> List[Route]:
        return self._routes

    def get_role(self) -> AssumableRole:
        return AssumableRole(**json.loads(request.headers.get('ActiveRole')))

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
    def build_response() -> any:
        """Builds a FiggyResponse from the current return type"""

        def fwrap(func):
            @wraps(func)
            def wrapped_f(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)

                    if result is None:
                        result = {}

                    if isinstance(result, FiggyResponse):
                        return Response(result.json(), content_type=Controller.JSON_CONTENT_TYPE)

                    response = Response(FiggyResponse(data=result).json(), content_type=Controller.JSON_CONTENT_TYPE)
                    log.info(f"RETURNING RESPONSE: {response.data}")
                    return response
                except ClientError as e:
                    log.exception(e)
                    # If we get a AccessDenied exception to decrypt this parameter, it must be encrypted
                    if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                        return ResponseBuilder.build(FiggyResponse.fig_missing())
                    elif "AccessDeniedException" == e.response['Error']['Code']:
                        return ResponseBuilder.build(FiggyResponse.no_access_to_parameter())
                    elif "ParameterNotFound" == e.response['Error']['Code']:
                        return ResponseBuilder.build(FiggyResponse.fig_missing())
                except botocore.exceptions.ParamValidationError as e2:
                    log.warning(f'Caught parameter validation exception: ${e2}')
                    log.exception(e2)
                    return ResponseBuilder.build(FiggyResponse.fig_invalid())
                except BaseException as e1:
                    log.warning('Caught unexpected exception: {e1}')
                    log.exception(e1)

            return wrapped_f

        return fwrap
