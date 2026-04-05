from typing import Callable
from .wrappers import Request, Response


class CORSMiddleware:
    def __init__(self,
                 allow_origins: list[str] = None,
                 allow_methods: list[str] = None,
                 allow_headers: list[str] = None,
                 allow_credentials: bool = False,
                 max_age: int = 600):
        self._origins = allow_origins or ["*"]
        self._methods = allow_methods or ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        self._headers = allow_headers or ["Content-Type", "Authorization", "X-CSRF-Token"]
        self._credentials = allow_credentials
        self._max_age = max_age

    def _origin_allowed(self, origin: str) -> bool:
        if "*" in self._origins:
            return True
        return origin in self._origins

    async def __call__(self, request: Request, next: Callable) -> Response:
        origin = request.headers.get("Origin", "")

        if request.method == "OPTIONS":
            resp = Response(body="", status=204)
            self._apply_headers(resp, origin)
            resp.headers["Access-Control-Max-Age"] = str(self._max_age)
            return resp

        resp = await next(request)
        self._apply_headers(resp, origin)
        return resp

    def _apply_headers(self, response: Response, origin: str):
        if self._origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self._methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self._headers)
        if self._credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"