import inspect
from typing import Callable


class WebSocket:
    def __init__(self, scope: dict, receive: Callable, send: Callable):
        self._scope = scope
        self._receive = receive
        self._send = send
        self.path = scope.get("path", "/")
        self.headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
        self.query_params = scope.get("query_string", b"").decode()

    async def accept(self):
        await self._send({"type": "websocket.accept"})

    async def send_text(self, data: str):
        await self._send({"type": "websocket.send", "text": data})

    async def send_bytes(self, data: bytes):
        await self._send({"type": "websocket.send", "bytes": data})

    async def receive_text(self) -> str | None:
        event = await self._receive()
        if event["type"] == "websocket.disconnect":
            return None
        return event.get("text", "")

    async def receive_bytes(self) -> bytes | None:
        event = await self._receive()
        if event["type"] == "websocket.disconnect":
            return None
        return event.get("bytes", b"")

    async def close(self, code: int = 1000):
        await self._send({"type": "websocket.close", "code": code})

    def __repr__(self):
        return f"<WebSocket {self.path}>"


class WebSocketRoute:
    def __init__(self, path: str, handler: Callable):
        import re
        self.path = path
        self.handler = handler
        regex = re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", path)
        self.regex = re.compile(f"^{regex}$")

    def match(self, path: str) -> dict | None:
        m = self.regex.match(path)
        return m.groupdict() if m else None


class WebSocketRouter:
    def __init__(self):
        self._routes: list[WebSocketRoute] = []

    def add(self, path: str, handler: Callable):
        self._routes.append(WebSocketRoute(path, handler))

    def resolve(self, path: str) -> tuple[Callable | None, dict]:
        for route in self._routes:
            params = route.match(path)
            if params is not None:
                return route.handler, params
        return None, {}