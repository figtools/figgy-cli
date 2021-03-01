from dataclasses import dataclass


@dataclass
class Account:
    account: str

    def __str__(self):
        return self.account

    def __eq__(self, other):
        return self.account == other.account
