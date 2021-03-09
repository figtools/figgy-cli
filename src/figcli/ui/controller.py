import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from typing import List
from botocore.exceptions import ClientError
from pydantic import BaseModel

from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.route import Route
from flask import make_response, Response

log = logging.getLogger(__name__)


class Controller:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self._routes: List[Route] = []

    def routes(self) -> List[Route]:
        return self._routes

    # @staticmethod
    # def handle_errors(func):
    #     """
    #     Decorator that adds logging around function execution and function parameters.
    #     """
    #
    #     def wrapper(*args, **kwargs):
    #         try:
    #             return func(*args, **kwargs)
    #         except ClientError as e:
    #             error = e.response['Error']
    #             if "AccessDeniedException" == error.get('Code') and \
    #                     "ciphertext refers to" in error.get('Message'):
    #                 return make_response(Error.KMS_DENIED)
    #             else:
    #                 raise
    #
    #     return wrapper

    @staticmethod
    def return_json(func):
        """
        Converts the response to JSON unless it's a string, then we just return the string.
        """

        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, str):
                return result
            elif isinstance(result, BaseModel):
                return result.json()
            else:
                return json.dumps(result)

        return wrapper

    @staticmethod
    def client_cache(seconds=15, content_type='application/json; charset=utf-8'):
        """ Flask decorator that allow to set Expire and Cache headers. """

        def fwrap(f):
            @wraps(f)
            def wrapped_f(*args, **kwargs):
                jsonWrappedF = Controller.return_json(f)
                result = jsonWrappedF(*args, **kwargs)
                then = datetime.now() + timedelta(seconds=seconds)
                rsp = Response(result, content_type=content_type)
                rsp.headers.add('Expires', then.strftime("%a, %d %b %Y %H:%M:%S GMT"))
                rsp.headers.add('Cache-Control', 'public,max-age=%d' % int(seconds))
                return rsp

            return wrapped_f

        return fwrap

    @staticmethod
    def build_response():
        """Builds a FiggyResponse from the current return type"""

        def fwrap(func):
            @wraps(func)
            def wrapped_f(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return FiggyResponse(data=result)
                except ClientError as e:
                    # If we get a AccessDenied exception to decrypt this parameter, it must be encrypted
                    if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                        return FiggyResponse.no_decrypt_access()
                    elif "AccessDeniedException" == e.response['Error']['Code']:
                        return FiggyResponse.no_access_to_parameter()

            return wrapped_f

        return fwrap
