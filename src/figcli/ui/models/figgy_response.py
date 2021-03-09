from typing import Optional, Dict, Any

from pydantic import BaseModel

from figcli.ui.errors import Error
from figcli.ui.models.figgy_error import FiggyError


class FiggyResponse(BaseModel):
    data: Any
    error: Optional[FiggyError]

    @staticmethod
    def from_dict(item: Dict) -> "FiggyResponse":
        return FiggyResponse(data=item)

    @staticmethod
    def no_decrypt_access() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.KMS_DENIED))

    @staticmethod
    def no_access_to_parameter() -> "FiggyResponse":
        return FiggyResponse(error=FiggyError(**Error.GET_PARAM_DENIED))
