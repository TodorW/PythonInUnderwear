import re
from typing import Callable, Optional


class Route:
    def __init__(self, pattern: str, handler: Callable, methods: list[str]):
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        regex = re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern)
        self.regex = re.compile(f"^{regex}$")

    def match(self, path: str, method: str) -> Optional[dict]:
        if method.upper() not in self.methods:
            return None
        m = self.regex.match(path)
        return m.groupdict() if m else None

    def __repr__(self):
        return f"<Route {self.methods} {self.regex.pattern}>"


class Router:
    def __init__(self):
        self._routes: list[Route] = []

    def add_route(self, pattern: str, handler: Callable, methods: list[str]):
        self._routes.append(Route(pattern, handler, methods))

    def resolve(self, path: str, method: str) -> tuple[Optional[Callable], dict]:
        for route in self._routes:
            params = route.match(path, method)
            if params is not None:
                return route.handler, params
        return None, {}

    def __repr__(self):
        return f"<Router routes={len(self._routes)}>"