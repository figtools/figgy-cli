from typing import Optional

from pydantic import BaseModel


class OktaSession(BaseModel):
    session_id: Optional[str]
    session_token: Optional[str]
