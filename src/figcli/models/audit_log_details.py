from typing import Optional

from pydantic import BaseModel, validator


class AuditLogDetails(BaseModel):
    parameter_name: str
    time: int
    action: str
    user: str
    value: Optional[str]
    decrypted_value: Optional[str]
    type: Optional[str]
    description: Optional[str]
    version: Optional[int]
    key_id: Optional[str]
