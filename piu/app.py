import asyncio
import inspect
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

from .auth import current_user, is_authenticated, login_user, logout_user, require_auth
from .config import Config
from .csrf import CSRFMiddleware, csrf_input
from .helpers import status_text
from .middleware import MiddlewareStack
from .ratelimit import RateLimitMiddleware, rate_limit
from .routing import Blueprint, Router
from .serving import run_dev_server
from .sessions import SessionMiddleware
from .static import serve_static
from .templating import TemplateEngine
from .wrappers import Request, Response


class PIU:
    def __init__(self, template_dir: str = None,
                 static_dir: str = None,
                 static_url: str = None,
                 config: dict = None):
        self.config = Config(config)
        self.router = Router()
        self.middleware = MiddlewareStack()
        self._template_dir = template_dir or self.config["TEMPLATE_DIR"]
        self._static_dir   = static_dir   or self.config["STATIC_DIR"]
        self._static_url   = static_url   or self.config["STATIC_URL"]
        self._template_engine: Optional[TemplateEngine] = None
        self._error_handlers: dict[int, Callable] = {}

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        await self.asgi(scope, receive, send)

    def route(self, path: str, methods: list[str] = ["GET"]):
        def decorator(fn: Callable):
            self.router.add_route(path, fn, methods)
            return fn
        return decorator

    def get(self, path: str):    return self.route(path, methods=["GET"])
    def post(self, path: str):   return self.route(path, methods=["POST"])
    def put(self, path: str):    return self.route(path, methods=["PUT"])
    def patch(self, path: str):  return self.route(path, methods=["PATCH"])
    def delete(self, path: str): return self.route(path, methods=["DELETE"])

    def register(self, blueprint: Blueprint, prefix: str = None):
        bp_prefix = (prefix or blueprint.prefix).rstrip("/")
        for path, handler, methods in blueprint._routes:
            full_path = bp_prefix + ("" if path == "/" else path)
            self.router.add_route(full_path, handler, methods)

    def errorhandler(self, status_code: int):
        def decorator(fn: Callable):
            self._error_handlers[status_code] = fn
            return fn
        return decorator

    async def _handle_error(self, request: Request, status: int, error: Exception = None) -> Response:
        handler = self._error_handlers.get(status)
        if handler:
            result = handler(request, error) if not inspect.iscoroutinefunction(handler) \
                else await handler(request, error)
            return result if isinstance(result, Response) else Response(body=result, status=status)
        return Response(body=f"{status} {status_text(status)}", status=status)

    def render(self, template_name: str, **context) -> Response:
        if self._template_engine is None:
            self._template_engine = TemplateEngine(self._template_dir)
        html = self._template_engine.render(template_name, **context)
        return Response(body=html, content_type="text/html")

    async def _dispatch(self, request: Request) -> Response:
        static_resp = serve_static(request.path, self._static_dir, self._static_url)
        if static_resp is not None:
            return static_resp

        handler, path_params = self.router.resolve(request.path, request.method)

        if handler is None:
            return await self._handle_error(request, 404)

        async def call_handler(req: Request) -> Response:
            try:
                result = await handler(req, **path_params) \
                    if inspect.iscoroutinefunction(handler) \
                    else handler(req, **path_params)
                return result if isinstance(result, Response) else Response(body=result)
            except Exception as e:
                return await self._handle_error(req, 500, e)

        return await self.middleware.run(request, call_handler)

    def _finalize(self, response: Response) -> Response:
        for k, v in response._cookie_headers():
            response.headers[k] = v
        return response

    def wsgi(self, environ: dict, start_response: Callable):
        parsed = urlparse(environ.get("PATH_INFO", "/"))
        query = parse_qs(environ.get("QUERY_STRING", ""))
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length) if length else b""

        headers = {
            k[5:].replace("_", "-").title(): v
            for k, v in environ.items() if k.startswith("HTTP_")
        }

        request = Request(
            method=environ.get("REQUEST_METHOD", "GET"),
            path=parsed.path, headers=headers,
            body=body, query_params=query,
        )

        response = self._finalize(asyncio.run(self._dispatch(request)))
        status_str = f"{response.status} {status_text(response.status)}"
        resp_headers = [("Content-Type", response.content_type)]
        for k, v in response.headers.items():
            resp_headers.append((k, v))

        start_response(status_str, resp_headers)
        return [response.body]

    async def asgi(self, scope: dict, receive: Callable, send: Callable):
        if scope["type"] != "http":
            return

        body = b""
        while True:
            event = await receive()
            body += event.get("body", b"")
            if not event.get("more_body", False):
                break

        query = parse_qs(scope.get("query_string", b"").decode())
        headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}

        request = Request(
            method=scope.get("method", "GET"),
            path=scope.get("path", "/"),
            headers=headers, body=body, query_params=query,
        )

        response = self._finalize(await self._dispatch(request))

        await send({
            "type": "http.response.start",
            "status": response.status,
            "headers": [
                [b"content-type", response.content_type.encode()],
                *[[k.encode(), v.encode()] for k, v in response.headers.items()]
            ],
        })
        await send({"type": "http.response.body", "body": response.body})

    def run(self, host: str = None, port: int = None, reload: bool = None):
        run_dev_server(
            self,
            host   = host   or self.config.get("HOST", "127.0.0.1"),
            port   = port   or self.config.get("PORT", 5000),
            reload = reload if reload is not None else self.config.get("DEBUG", False),
        )

    def __repr__(self):
        return f"<PIU routes={len(self.router._routes)} middleware={len(self.middleware._middlewares)}>"