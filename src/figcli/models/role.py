from dataclasses import dataclass


@dataclass
class Role:
    role: str
    full_name: str

    def __str__(self):
        return self.role

    def __eq__(self, other):
        return self.role == other.role

    def __hash__(self):
        return hash(self.role)
