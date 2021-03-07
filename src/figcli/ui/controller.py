import logging

from typing import List
from botocore.exceptions import ClientError

from figcli.ui.http_errors import Error
from figcli.ui.route import Route
from flask import make_response

log = logging.getLogger(__name__)


class Controller:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self._routes: List[Route] = []

    def routes(self) -> List[Route]:
        return self._routes

    @staticmethod
    def handle_errors(func):
        """
        Decorator that adds logging around function execution and function parameters.
        """

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                error = e.response['Error']
                if "AccessDeniedException" == error.get('Code') and \
                        "ciphertext refers to" in error.get('Message'):
                    return make_response(Error.KMS_DENIED)
                else:
                    raise

        return wrapper

    @staticmethod
    def return_json(func):
        """
        Assumes the returned OBJ from the controller extends BaseModel therefore the .json() method can be called
        and we will return a JSON representation of the returned object.
        """

        def wrapper(*args, **kwargs):
                return func(*args, **kwargs).json()

        return wrapper
