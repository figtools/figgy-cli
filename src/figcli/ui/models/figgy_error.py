from pydantic import BaseModel


class FiggyError(BaseModel):
    error_code: str
    message: str
    status_code: int
    is_error: bool = True