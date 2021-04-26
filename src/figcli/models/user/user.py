from typing import List

from pydantic import BaseModel

from figcli.models.assumable_role import AssumableRole
from figcli.models.role import Role


class User(BaseModel):
    name: str
    role: Role
    assumable_roles: List[AssumableRole]
    enabled_regions: List[str]
