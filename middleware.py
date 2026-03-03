import inspect
from typing import Callable

from .wrappers import Request, Response


class MiddlewareStack:
    def __init__(self):
        self._middlewares: list[Callable] = []

    def use(self, fn: Callable):
        """Register a middleware.
        Signature: fn(request, next) -> Response
        The middleware must call next(request) to continue the chain.
        """
        self._middlewares.append(fn)

    async def run(self, request: Request, final_handler: Callable) -> Response:
        idx = 0
        middlewares = self._middlewares

        async def next_fn(req: Request) -> Response:
            nonlocal idx
            if idx < len(middlewares):
                mw = middlewares[idx]
                idx += 1
                if inspect.iscoroutinefunction(mw):
                    return await mw(req, next_fn)
                else:
                    return mw(req, next_fn)
            else:
                if inspect.iscoroutinefunction(final_handler):
                    return await final_handler(req)
                else:
                    return final_handler(req)

        return await next_fn(request)

    def __repr__(self):
        return f"<MiddlewareStack count={len(self._middlewares)}>"