from typing import List


class CliCommand:
    command: str
    hash_key: str
    aliases: List[str]

    def __init__(self, command: str, hash_key=None, aliases: List[str] = None):
        self.command = command
        self.hash_key = hash_key or command
        self.aliases = aliases or []

    @property
    def name(self):
        return self.command

    @property
    def standardized_name(self):
        return self.command.replace("-", "_")

    def __str__(self):
        return self.command

    def __hash__(self):
        return hash(self.hash_key)

    def __eq__(self, o):
        return self.command == o

    def __repr__(self):
        return self.command
