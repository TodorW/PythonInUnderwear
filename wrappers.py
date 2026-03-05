import json
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import parse_qs


class Request:
    def __init__(self, method: str, path: str, headers: dict,
                 body: bytes = b"", query_params: dict = None):
        self.method = method.upper()
        self.path = path
        self.headers = headers
        self.body = body
        self.query_params = query_params or {}
        self._json = None
        self._cookies = None

    def json(self) -> Any:
        if self._json is None:
            self._json = json.loads(self.body.decode("utf-8"))
        return self._json

    def form(self) -> dict:
        return parse_qs(self.body.decode("utf-8"))

    @property
    def cookies(self) -> dict:
        if self._cookies is None:
            raw = self.headers.get("Cookie", self.headers.get("cookie", ""))
            sc = SimpleCookie()
            sc.load(raw)
            self._cookies = {k: v.value for k, v in sc.items()}
        return self._cookies

    def __repr__(self):
        return f"<Request {self.method} {self.path}>"


class Response:
    def __init__(self, body: Any = "", status: int = 200,
                 content_type: str = "text/html", headers: dict = None):
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type
        self._cookies = SimpleCookie()

        if isinstance(body, (dict, list)):
            self.body = json.dumps(body).encode("utf-8")
            self.content_type = "application/json"
        elif isinstance(body, str):
            self.body = body.encode("utf-8")
        elif isinstance(body, bytes):
            self.body = body
        else:
            self.body = str(body).encode("utf-8")

    @classmethod
    def json(cls, data: Any, status: int = 200) -> "Response":
        return cls(body=data, status=status, content_type="application/json")

    @classmethod
    def redirect(cls, location: str, status: int = 302) -> "Response":
        r = cls(body="", status=status)
        r.headers["Location"] = location
        return r

    def set_cookie(self, key: str, value: str, max_age: int = None,
                   path: str = "/", httponly: bool = True,
                   secure: bool = False, samesite: str = "Lax"):
        self._cookies[key] = value
        m = self._cookies[key]
        if max_age is not None:
            m["max-age"] = max_age
        m["path"] = path
        m["httponly"] = httponly
        m["secure"] = secure
        m["samesite"] = samesite

    def delete_cookie(self, key: str, path: str = "/"):
        self.set_cookie(key, "", max_age=0, path=path)

    def _cookie_headers(self) -> list[tuple]:
        return [("Set-Cookie", m.OutputString()) for m in self._cookies.values()]

    def __repr__(self):
        return f"<Response {self.status}>"