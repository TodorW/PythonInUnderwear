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


class Blueprint:
    """A group of routes that can be registered on a PIU app with a URL prefix."""

    def __init__(self, name: str, prefix: str = ""):
        self.name = name
        self.prefix = prefix.rstrip("/")
        self._routes: list[tuple[str, Callable, list[str]]] = []

    def route(self, path: str, methods: list[str] = ["GET"]):
        def decorator(fn: Callable):
            self._routes.append((path, fn, methods))
            return fn
        return decorator

    def get(self, path: str):
        return self.route(path, methods=["GET"])

    def post(self, path: str):
        return self.route(path, methods=["POST"])

    def put(self, path: str):
        return self.route(path, methods=["PUT"])

    def patch(self, path: str):
        return self.route(path, methods=["PATCH"])

    def delete(self, path: str):
        return self.route(path, methods=["DELETE"])

    def __repr__(self):
        return f"<Blueprint '{self.name}' prefix='{self.prefix}' routes={len(self._routes)}>"