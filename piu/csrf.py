import os
import hmac
import hashlib
from typing import Callable

from .wrappers import Request, Response

CSRF_SESSION_KEY = "_csrf_token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _generate_token() -> str:
    return os.urandom(32).hex()


def _tokens_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


class CSRFMiddleware:
    def __init__(self, exempt_paths: list[str] = None):
        """
        Args:
            exempt_paths: List of URL path prefixes to skip CSRF checks on.
                          Useful for API routes using token auth instead of sessions.
                          e.g. ["/api/", "/webhook"]
        """
        self._exempt = exempt_paths or []

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(p) for p in self._exempt)

    async def __call__(self, request: Request, next: Callable) -> Response:
        if not hasattr(request, "session"):
            raise RuntimeError(
                "CSRFMiddleware requires SessionMiddleware to run first. "
                "Register SessionMiddleware before CSRFMiddleware."
            )

        
        if CSRF_SESSION_KEY not in request.session:
            request.session[CSRF_SESSION_KEY] = _generate_token()

        token = request.session[CSRF_SESSION_KEY]

        
        request.csrf_token = token

        
        if request.method in UNSAFE_METHODS and not self._is_exempt(request.path):
            
            submitted = (
                request.headers.get("X-Csrf-Token")
                or request.headers.get("X-CSRF-Token")
                or request.form().get("_csrf_token", [None])[0]
            )
            if not submitted or not _tokens_equal(token, submitted):
                return Response(body="403 CSRF token invalid or missing.", status=403)

        return await next(request)


def csrf_input(token: str) -> str:
    """Return an HTML hidden input string for use in templates."""
    return f'<input type="hidden" name="_csrf_token" value="{token}">'