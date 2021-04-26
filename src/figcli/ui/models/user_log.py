from typing import Optional

from pydantic.main import BaseModel

from figcli.models.kms_key import KmsKey


class UserLog(BaseModel):
    user: str
    parameter: str
    time: int
    action: Optional[str]
    value: Optional[str]
    key: Optional[KmsKey]

    def __gt__(self, other):
        return self.time > other.time

    def __lt__(self, other):
        return self.time < other.time

    def __hash__(self):
        return hash(f'{self.user}--{self.parameter}--{self.time}--{self.action}')

# Functionality:
# - Find user logs via a search feature (in progress)
# - Find all secrets retrieved by user that have not been rotated since retrieved.
