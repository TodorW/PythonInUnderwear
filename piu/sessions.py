"""
Session middleware for PIU.
Sessions are stored as signed, base64-encoded JSON cookies.
No server-side storage needed — the cookie IS the session.

Requires: pip install cryptography
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Callable

from .wrappers import Request, Response


class Session(dict):
    """A dict subclass that tracks whether it has been modified."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.modified = True

    def __delitem__(self, key):
        super().__delitem__(key)
        self.modified = True

    def clear(self):
        super().clear()
        self.modified = True


class SessionMiddleware:
    COOKIE_NAME = "piu_session"

    def __init__(self, secret_key: str, max_age: int = 86400,
                 httponly: bool = True, secure: bool = False,
                 samesite: str = "Lax"):
        if not secret_key:
            raise ValueError("SessionMiddleware requires a non-empty secret_key.")
        self._secret = secret_key.encode()
        self._max_age = max_age
        self._httponly = httponly
        self._secure = secure
        self._samesite = samesite

    def _sign(self, data: str) -> str:
        sig = hmac.new(self._secret, data.encode(), hashlib.sha256).hexdigest()
        payload = base64.urlsafe_b64encode(data.encode()).decode()
        return f"{payload}.{sig}"

    def _unsign(self, token: str) -> dict | None:
        try:
            payload, sig = token.rsplit(".", 1)
            data = base64.urlsafe_b64decode(payload.encode()).decode()
            expected = hmac.new(self._secret, data.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None
            return json.loads(data)
        except Exception:
            return None

    async def __call__(self, request: Request, next: Callable) -> Response:
        raw = request.cookies.get(self.COOKIE_NAME)
        data = self._unsign(raw) if raw else None
        request.session = Session(data or {})

        response = await next(request)

        if request.session.modified:
            payload = json.dumps(dict(request.session), separators=(",", ":"))
            token = self._sign(payload)
            response.set_cookie(
                self.COOKIE_NAME, token,
                max_age=self._max_age,
                httponly=self._httponly,
                secure=self._secure,
                samesite=self._samesite,
            )

        return response