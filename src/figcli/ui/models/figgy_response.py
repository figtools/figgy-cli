from typing import Optional, Dict, Any, List

from pydantic import BaseModel, validator

from figcli.ui.errors import Error
from figcli.ui.models.figgy_error import FiggyError


class FiggyResponse(BaseModel):
    data: Any
    status_code: Optional[int]
    error: Optional[FiggyError]

    # set status_code by error's code mapping
    @validator('error', pre=True)
    def init_error(cls, value, values):
        if value:
            values['status_code'] = value.status_code

        return value

    @staticmethod
    def from_dict(item: Dict) -> "FiggyResponse":
        return FiggyResponse(data=item)

    @staticmethod
    def no_decrypt_access() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.KMS_DENIED))

    @staticmethod
    def no_access_to_parameter() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.PARAM_ACCESS_DENIED))

    @staticmethod
    def fig_missing() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.FIG_MISSING))

    @staticmethod
    def fig_invalid() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.FIG_INVALID))

    @staticmethod
    def mfa_required() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.MFA_REQUIRED))

    @staticmethod
    def force_reauth() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.FORCE_REAUTHENTICATION))

    @staticmethod
    def ots_missing() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.OTS_MISSING))

    @staticmethod
    def invalid_parameters(missing_parameters: List[str]) -> "FiggyResponse":
        error = FiggyError(**Error.BAD_REQUEST)
        error.message = error.message + f" The following request parameter(s) were expected but missing or invalid: " \
                                        f"{missing_parameters}"
        return FiggyResponse(error=error)

    @staticmethod
    def validation_error(error_msg: str):
        error = FiggyError(**Error.BAD_REQUEST)
        error.message = error.message + f' {error_msg}'
        return FiggyResponse(error=error)
