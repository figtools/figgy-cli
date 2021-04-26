from pydantic import BaseModel


class EncryptionKey(BaseModel):
    kms_key_id: str
    alias: str