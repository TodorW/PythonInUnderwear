"""
Auth utilities for PIU.

Provides:
  - @require_auth           — decorator that guards a route, redirects or 401s if not authed
  - @require_auth(role=...) — additionally checks request.user["role"]
  - login_user(request, user_data)   — store user in session
  - logout_user(request)             — clear user from session
  - current_user(request)            — retrieve user dict from session (or None)

Requires SessionMiddleware to be registered.

Example::

    @app.post("/login")
    def login(request):
        user = db.check_credentials(request.json())
        if not user:
            return Response(body="Bad credentials", status=401)
        login_user(request, {"id": user.id, "role": "admin"})
        return Response.redirect("/dashboard")

    @app.get("/dashboard")
    @require_auth
    def dashboard(request):
        return Response(body=f"Hello {current_user(request)['id']}")

    @app.get("/admin")
    @require_auth(role="admin")
    def admin_panel(request):
        ...
"""

import functools
import inspect
from typing import Callable

from .wrappers import Request, Response

SESSION_USER_KEY = "_auth_user"


# ── Session helpers ──────────────────────────────────────────

def login_user(request: Request, user_data: dict):
    """Store user data in the session."""
    _require_session(request)
    request.session[SESSION_USER_KEY] = user_data


def logout_user(request: Request):
    """Remove user data from the session."""
    _require_session(request)
    request.session.pop(SESSION_USER_KEY, None)


def current_user(request: Request) -> dict | None:
    """Return the logged-in user dict, or None."""
    _require_session(request)
    return request.session.get(SESSION_USER_KEY)


def is_authenticated(request: Request) -> bool:
    return current_user(request) is not None


def _require_session(request: Request):
    if not hasattr(request, "session"):
        raise RuntimeError(
            "Auth helpers require SessionMiddleware. "
            "Register it before using @require_auth."
        )


# ── @require_auth decorator ──────────────────────────────────

def require_auth(fn: Callable = None, *, role: str = None,
                 redirect_to: str = None, status: int = 401):
    """
    Guard a route handler. Can be used with or without arguments:

        @require_auth
        def view(request): ...

        @require_auth(role="admin", redirect_to="/login")
        def admin(request): ...

    Args:
        role:        If set, also checks request.session["_auth_user"]["role"].
        redirect_to: If set, returns a redirect instead of a 401/403 response.
        status:      Status code for unauthenticated responses (default 401).
                     Automatically becomes 403 when role check fails.
    """
    def decorator(handler: Callable):
        @functools.wraps(handler)
        async def wrapper(request: Request, *args, **kwargs):
            _require_session(request)
            user = current_user(request)

            if not user:
                return _deny(redirect_to, status, "401 Unauthorized.")

            if role and user.get("role") != role:
                return _deny(redirect_to, 403, f"403 Forbidden — requires role '{role}'.")

            if inspect.iscoroutinefunction(handler):
                return await handler(request, *args, **kwargs)
            return handler(request, *args, **kwargs)

        return wrapper

    # Support both @require_auth and @require_auth(role="admin")
    if fn is not None:
        return decorator(fn)
    return decorator


def _deny(redirect_to: str, status: int, message: str) -> Response:
    if redirect_to:
        return Response.redirect(redirect_to)
    return Response(body=message, status=status)