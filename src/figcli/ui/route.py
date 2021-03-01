from dataclasses import dataclass
from typing import Callable, List


@dataclass
class Route:
    def __init__(self, url_path: str, fn: Callable, methods: List[str]):
        self.url_path = url_path
        self.fn = fn
        self.methods = methods