import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from typing import List, Any
from botocore.exceptions import ClientError
from pydantic import BaseModel

from figcli.models.assumable_role import AssumableRole
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.route import Route
from flask import make_response, Response, request

log = logging.getLogger(__name__)
JSON_CONTENT_TYPE = 'application/json; charset=utf-8'

class Controller:
    def __init__(self, prefix: str, svc_registry: ServiceRegistry):
        self.prefix = prefix
        self._routes: List[Route] = []
        self._registry = svc_registry

    def _cfg(self):
        return self._registry.config_svc(self.get_role())
        # return self.registry.config_svc(self.context.defaults.assumable_roles[0])

    def _cfg_view(self):
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
                    log.info("Executing wrapped...")
                    result = func(*args, **kwargs) or {'response': '200'}
                    log.info(f"Got result: {result}")
                    return Response(FiggyResponse(data=result).json(), content_type=JSON_CONTENT_TYPE)
                except ClientError as e:
                    log.error(e)
                    # If we get a AccessDenied exception to decrypt this parameter, it must be encrypted
                    if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                        return Response(FiggyResponse.no_decrypt_access().json(), content_type=JSON_CONTENT_TYPE)
                    elif "AccessDeniedException" == e.response['Error']['Code']:
                        return Response(FiggyResponse.no_access_to_parameter().json(), content_type=JSON_CONTENT_TYPE)
                except BaseException as e1:
                    log.warning("Caught unexepcted exception")
                    log.error(e1)

            return wrapped_f

        return fwrap
