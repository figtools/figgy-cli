from typing import Optional

from pydantic import BaseModel


class Role(BaseModel):
    role: str
    full_name: Optional[str]

    def __str__(self):
        return self.role

    def __eq__(self, other):
        return self.role == other.role

    def __hash__(self):
        return hash(self.role)

