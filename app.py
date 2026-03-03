import asyncio
import inspect
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

from .helpers import status_text
from .middleware import MiddlewareStack
from .routing import Router
from .serving import run_dev_server
from .templating import TemplateEngine
from .wrappers import Request, Response


class PIU:
    def __init__(self, template_dir: str = "templates"):
        self.router = Router()
        self.middleware = MiddlewareStack()
        self._template_dir = template_dir
        self._template_engine: Optional[TemplateEngine] = None


    def route(self, path: str, methods: list[str] = ["GET"]):
        def decorator(fn: Callable):
            self.router.add_route(path, fn, methods)
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


    def render(self, template_name: str, **context) -> Response:
        if self._template_engine is None:
            self._template_engine = TemplateEngine(self._template_dir)
        html = self._template_engine.render(template_name, **context)
        return Response(body=html, content_type="text/html")


    async def _dispatch(self, request: Request) -> Response:
        handler, path_params = self.router.resolve(request.path, request.method)

        if handler is None:
            return Response(body="404 Not Found", status=404)

        async def call_handler(req: Request) -> Response:
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(req, **path_params)
                else:
                    result = handler(req, **path_params)
                return result if isinstance(result, Response) else Response(body=result)
            except Exception as e:
                return Response(body=f"500 Internal Server Error: {e}", status=500)

        return await self.middleware.run(request, call_handler)


    def wsgi(self, environ: dict, start_response: Callable):
        parsed = urlparse(environ.get("PATH_INFO", "/"))
        query = parse_qs(environ.get("QUERY_STRING", ""))
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length) if length else b""

        headers = {
            k[5:].replace("_", "-").title(): v
            for k, v in environ.items()
            if k.startswith("HTTP_")
        }

        request = Request(
            method=environ.get("REQUEST_METHOD", "GET"),
            path=parsed.path,
            headers=headers,
            body=body,
            query_params=query,
        )

        response = asyncio.run(self._dispatch(request))
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
            headers=headers,
            body=body,
            query_params=query,
        )

        response = await self._dispatch(request)

        await send({
            "type": "http.response.start",
            "status": response.status,
            "headers": [
                [b"content-type", response.content_type.encode()],
                *[[k.encode(), v.encode()] for k, v in response.headers.items()]
            ],
        })
        await send({"type": "http.response.body", "body": response.body})


    def run(self, host: str = "127.0.0.1", port: int = 5000):
        run_dev_server(self, host=host, port=port)

    def __repr__(self):
        return f"<PIU routes={len(self.router._routes)} middleware={len(self.middleware._middlewares)}>"