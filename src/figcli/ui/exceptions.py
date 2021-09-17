from typing import List


class CannotRetrieveMFAException(BaseException):
    pass


class InvalidCredentialsException(BaseException):
    pass


class BadRequestParameters(BaseException):
    message: str
    invalid_parameters: List[str]

    def __init__(self, message: str, invalid_parameters: List[str]):
        self.message = message
        self.invalid_parameters = invalid_parameters


class InvalidFiggyConfigurationException(BaseException):
    pass