import asyncio
import functools
import inspect
import time
from typing import Callable
from .wrappers import Request, Response


class _CacheEntry:
    def __init__(self, response: Response, ttl: float):
        self.response = response
        self.expires_at = time.monotonic() + ttl


_cache_store: dict[str, _CacheEntry] = {}


def cache(ttl: int = 60, key_func: Callable = None):
    """
    Cache a route's response for `ttl` seconds.
    By default the cache key is the request path.

    Usage::

        @app.get("/expensive")
        @cache(ttl=30)
        def expensive(request):
            ...

        # Custom cache key
        @app.get("/user/<id>")
        @cache(ttl=60, key_func=lambda req, **kw: f"user:{kw.get('id')}")
        def get_user(request, id):
            ...
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(request: Request, **path_params):
            key = key_func(request, **path_params) if key_func else request.path
            entry = _cache_store.get(key)

            if entry and time.monotonic() < entry.expires_at:
                cached = entry.response
                resp = Response(body=cached.body, status=cached.status,
                                content_type=cached.content_type)
                resp.headers["X-Cache"] = "HIT"
                return resp

            if inspect.iscoroutinefunction(fn):
                result = await fn(request, **path_params)
            else:
                result = fn(request, **path_params)

            resp = result if isinstance(result, Response) else Response(body=result)
            _cache_store[key] = _CacheEntry(resp, ttl)
            resp.headers["X-Cache"] = "MISS"
            return resp

        return wrapper
    return decorator


def clear_cache(key: str = None):
    """Clear a specific cache key or the entire cache."""
    if key:
        _cache_store.pop(key, None)
    else:
        _cache_store.clear()