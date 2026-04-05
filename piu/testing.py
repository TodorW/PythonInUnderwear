import asyncio
import json as _json
from http.cookies import SimpleCookie
from urllib.parse import urlencode, parse_qs

from .wrappers import Request, Response


class TestClient:
    def __init__(self, app):
        self._app = app
        self._cookies: dict[str, str] = {}
        self._loop = asyncio.new_event_loop()

    def _extract_cookies(self, response: Response):
        for key, val in response.headers.items():
            if key.lower() == "set-cookie":
                for cookie_str in val.split("\n"):
                    sc = SimpleCookie()
                    sc.load(cookie_str.strip())
                    for name, morsel in sc.items():
                        max_age = morsel.get("max-age")
                        if max_age is not None and str(max_age) == "0":
                            self._cookies.pop(name, None)
                        else:
                            self._cookies[name] = morsel.value

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self._cookies.items())

    def _request(self, method: str, path: str,
                 headers: dict = None,
                 body: bytes = b"",
                 query: dict = None) -> "TestResponse":
        hdrs = dict(headers or {})
        if self._cookies:
            hdrs["Cookie"] = self._cookie_header()

        # Always normalize query values to lists, matching parse_qs output
        normalized: dict = {}
        for k, v in (query or {}).items():
            if isinstance(v, list):
                normalized[k] = v
            else:
                normalized[k] = [str(v)]

        req = Request(
            method=method,
            path=path,
            headers=hdrs,
            body=body,
            query_params=normalized,
        )

        raw: Response = self._loop.run_until_complete(self._app._dispatch(req))
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

    def options(self, path: str, headers: dict = None) -> "TestResponse":
        return self._request("OPTIONS", path, headers=headers)

    def close(self):
        self._loop.close()

    def __del__(self):
        try:
            if not self._loop.is_closed():
                self._loop.close()
        except Exception:
            pass


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