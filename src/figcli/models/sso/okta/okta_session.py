from pydantic import BaseModel


class OktaSession(BaseModel):
    session_id: str
    session_token: str
