from pydantic import BaseModel


class Account(BaseModel):
    account: str

    def __str__(self):
        return self.account

    def __eq__(self, other):
        return self.account == other.account
