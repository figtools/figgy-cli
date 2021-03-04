from typing import Callable, List


class Route:
    def __init__(self, url_path: str, fn: Callable, methods: List[str]):
        self.url_path = url_path
        self.fn = fn
        self.methods = methods
