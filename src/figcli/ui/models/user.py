from dataclasses import dataclass
from typing import List

from figcli.models.assumable_role import AssumableRole
from figcli.models.role import Role


@dataclass
class User:
    name: str
    role: Role
    assumable_roles: List[AssumableRole]
