import logging
import sys
import time
from typing import Callable
from .wrappers import Request, Response

_LEVEL_COLORS = {
    "DEBUG":    "\033[36m",
    "INFO":     "\033[32m",
    "WARNING":  "\033[33m",
    "ERROR":    "\033[31m",
    "CRITICAL": "\033[35m",
}
_RESET = "\033[0m"
_BOLD  = "\033[1m"


class PIUFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelname, "")
        level = f"{color}{_BOLD}{record.levelname:<8}{_RESET}"
        msg = super().format(record)
        return f"{level} {msg}"


def get_logger(name: str = "piu") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(PIUFormatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


logger = get_logger("piu")


class LoggingMiddleware:
    """
    Structured request/response logger middleware.

    Usage::

        from piu.logging import LoggingMiddleware
        app.middleware.use(LoggingMiddleware())
    """
    def __init__(self, log_headers: bool = False):
        self._log_headers = log_headers
        self._logger = get_logger("piu.access")

    async def __call__(self, request: Request, next: Callable) -> Response:
        start = time.monotonic()
        response = await next(request)
        duration = (time.monotonic() - start) * 1000

        status = response.status
        color = "\033[32m" if status < 400 else "\033[31m" if status >= 500 else "\033[33m"
        status_str = f"{color}{status}{_RESET}"

        self._logger.info(
            f"{_BOLD}{request.method:<7}{_RESET} {request.path:<40} "
            f"{status_str}  {duration:.1f}ms"
        )

        if self._log_headers:
            for k, v in request.headers.items():
                self._logger.debug(f"  {k}: {v}")

        return response