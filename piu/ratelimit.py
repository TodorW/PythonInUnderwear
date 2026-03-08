import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable

from .wrappers import Request, Response




class AbstractRateLimitStore(ABC):
    @abstractmethod
    def hit(self, key: str, window: int) -> int:
        """Record a hit for key within the window. Returns current hit count."""

    @abstractmethod
    def reset(self, key: str):
        """Clear all hits for a key."""


class InMemoryStore(AbstractRateLimitStore):
    """Sliding window counter stored in-process. Not suitable for multi-process deployments."""

    def __init__(self):
        
        self._hits: dict[str, list[float]] = defaultdict(list)

    def hit(self, key: str, window: int) -> int:
        now = time.monotonic()
        cutoff = now - window
        hits = self._hits[key]
        
        self._hits[key] = [t for t in hits if t > cutoff]
        self._hits[key].append(now)
        return len(self._hits[key])

    def reset(self, key: str):
        self._hits.pop(key, None)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("Remote-Addr", "unknown")


def _rate_limit_response(limit: int, window: int) -> Response:
    resp = Response(
        body=f"429 Too Many Requests — limit is {limit} per {window}s.",
        status=429,
    )
    resp.headers["Retry-After"] = str(window)
    return resp




class RateLimitMiddleware:
    def __init__(self, limit: int, window: int,
                 store: AbstractRateLimitStore = None,
                 key_func: Callable = None):
        """
        Args:
            limit:    Max requests allowed per window.
            window:   Time window in seconds.
            store:    Custom store (defaults to InMemoryStore).
            key_func: fn(request) -> str to derive rate limit key.
                      Defaults to client IP.
        """
        self._limit = limit
        self._window = window
        self._store = store or InMemoryStore()
        self._key_func = key_func or _get_client_ip

    async def __call__(self, request: Request, next: Callable) -> Response:
        key = f"global:{self._key_func(request)}"
        count = self._store.hit(key, self._window)
        if count > self._limit:
            return _rate_limit_response(self._limit, self._window)
        return await next(request)




_route_store = InMemoryStore()


def rate_limit(limit: int, window: int,
               store: AbstractRateLimitStore = None,
               key_func: Callable = None):
    """Decorator to apply a rate limit to a specific route handler.

    Example::

        @app.post("/login")
        @rate_limit(limit=5, window=60)
        def login(request):
            ...
    """
    _store = store or _route_store
    _key_fn = key_func or _get_client_ip

    def decorator(fn: Callable):
        import inspect
        import functools

        @functools.wraps(fn)
        async def wrapper(request: Request, *args, **kwargs):
            key = f"{fn.__name__}:{_key_fn(request)}"
            count = _store.hit(key, window)
            if count > limit:
                return _rate_limit_response(limit, window)
            if inspect.iscoroutinefunction(fn):
                return await fn(request, *args, **kwargs)
            return fn(request, *args, **kwargs)

        return wrapper
    return decorator