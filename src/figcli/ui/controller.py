from dataclasses import dataclass
from typing import List
from figcli.ui.route import Route


@dataclass
class Controller:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self._routes: List[Route] = []

    def routes(self) -> List[Route]:
        return self._routes
