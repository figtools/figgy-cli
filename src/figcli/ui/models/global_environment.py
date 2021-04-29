from pydantic import BaseModel

from figcli.models.assumable_role import AssumableRole


class GlobalEnvironment(BaseModel):
    role: AssumableRole
    region: str

    def cache_key(self):
        return f'{self.role.role.full_name}-{self.region}'

    def __hash__(self):
        return hash(f'{self.role.__hash__}-{self.region}')
