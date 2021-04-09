from typing import Any

from pydantic.main import BaseModel


class PaginatedResponse(BaseModel):
    data: Any
    total: int
    page_size: int
    page_number: int
