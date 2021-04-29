from pydantic import BaseModel


class KmsKey(BaseModel):
    id: str
    alias: str
