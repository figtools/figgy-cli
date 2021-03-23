from typing import List

from pydantic import BaseModel

from figcli.models.assumable_role import AssumableRole
from figcli.models.kms_key import KmsKey


class AuthedRole(BaseModel):
    assumable_role: AssumableRole
    authed_kms_keys: List[KmsKey]
    authed_namespaces: List[str]
