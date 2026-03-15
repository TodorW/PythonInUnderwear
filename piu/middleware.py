import inspect
from typing import Callable

from .wrappers import Request, Response


class MiddlewareStack:
    def __init__(self):
        self._middlewares: list[Callable] = []

    def use(self, fn: Callable):
        self._middlewares.append(fn)

    async def run(self, request: Request, final_handler: Callable) -> Response:
        middlewares = self._middlewares
        n = len(middlewares)

        async def call(idx: int, req: Request) -> Response:
            if idx == n:
                if inspect.iscoroutinefunction(final_handler):
                    return await final_handler(req)
                return final_handler(req)

            mw = middlewares[idx]

            async def next_fn(r: Request) -> Response:
                return await call(idx + 1, r)

            if inspect.iscoroutinefunction(mw):
                return await mw(req, next_fn)

            result = mw(req, next_fn)
            if inspect.isawaitable(result):
                return await result
            return result

        return await call(0, request)

    def __repr__(self):
        return f"<MiddlewareStack count={len(self._middlewares)}>"