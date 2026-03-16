import asyncio
import json as _json
from urllib.parse import urlencode

from .wrappers import Request, Response


class TestClient:
    def __init__(self, app):
        self._app = app
        self._cookies: dict[str, str] = {}

    def _extract_cookies(self, response: Response):
        for key, val in response.headers.items():
            if key.lower() == "set-cookie":
                for cookie_str in val.split("\n"):
                    parts = [p.strip() for p in cookie_str.split(";")]
                    if not parts:
                        continue
                    name, _, value = parts[0].partition("=")
                    max_age = None
                    for part in parts[1:]:
                        if part.lower().startswith("max-age="):
                            try:
                                max_age = int(part.split("=", 1)[1])
                            except ValueError:
                                pass
                    if max_age == 0:
                        self._cookies.pop(name.strip(), None)
                    else:
                        self._cookies[name.strip()] = value.strip()

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self._cookies.items())

    def _request(self, method: str, path: str,
                 headers: dict = None,
                 body: bytes = b"",
                 query: dict = None) -> "TestResponse":
        hdrs = dict(headers or {})
        if self._cookies:
            hdrs.setdefault("Cookie", self._cookie_header())

        req = Request(
            method=method,
            path=path,
            headers=hdrs,
            body=body,
            query_params=query or {},
        )

        loop = asyncio.new_event_loop()
        try:
            raw: Response = loop.run_until_complete(self._app._dispatch(req))
        finally:
            loop.close()

        raw = self._app._finalize(raw)
        self._extract_cookies(raw)
        return TestResponse(raw)

    def get(self, path: str, query: dict = None, headers: dict = None) -> "TestResponse":
        return self._request("GET", path, headers=headers, query=query)

    def post(self, path: str, json=None, data: dict = None,
             body: bytes = b"", headers: dict = None) -> "TestResponse":
        hdrs = dict(headers or {})
        if json is not None:
            body = _json.dumps(json).encode()
            hdrs["Content-Type"] = "application/json"
        elif data is not None:
            body = urlencode(data).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        return self._request("POST", path, headers=hdrs, body=body)

    def put(self, path: str, json=None, body: bytes = b"",
            headers: dict = None) -> "TestResponse":
        hdrs = dict(headers or {})
        if json is not None:
            body = _json.dumps(json).encode()
            hdrs["Content-Type"] = "application/json"
        return self._request("PUT", path, headers=hdrs, body=body)

    def patch(self, path: str, json=None, body: bytes = b"",
              headers: dict = None) -> "TestResponse":
        hdrs = dict(headers or {})
        if json is not None:
            body = _json.dumps(json).encode()
            hdrs["Content-Type"] = "application/json"
        return self._request("PATCH", path, headers=hdrs, body=body)

    def delete(self, path: str, headers: dict = None) -> "TestResponse":
        return self._request("DELETE", path, headers=headers)


class TestResponse:
    def __init__(self, response: Response):
        self._raw = response
        self.status = response.status
        self.headers = response.headers
        self.content_type = response.content_type
        self.body = response.body

    def text(self) -> str:
        return self.body.decode("utf-8")

    def json(self):
        return _json.loads(self.body)

    def __repr__(self):
        return f"<TestResponse {self.status}>"