import inspect
import functools
from typing import Any, Callable, get_type_hints
from .wrappers import Request, Response


class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def _coerce(value: Any, annotation) -> Any:
    if annotation is inspect.Parameter.empty or annotation is Any:
        return value
    if isinstance(value, annotation):
        return value
    try:
        return annotation(value)
    except (ValueError, TypeError):
        raise ValueError(f"Expected {annotation.__name__}, got {type(value).__name__}")


def validate(fn: Callable):
    """
    Decorator that validates and coerces incoming JSON body fields
    against the handler's type hints.

    Usage::

        @app.post("/users")
        @validate
        def create_user(request: Request, name: str, age: int):
            return Response.json({"name": name, "age": age})

    PIU will parse the JSON body and inject matching fields as kwargs,
    coercing types automatically. Returns 422 with error details on failure.
    """
    hints = get_type_hints(fn)
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    async def wrapper(request: Request, **path_params):
        params = {}
        errors = {}

        try:
            body = request.json() if request.body else {}
        except Exception:
            body = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("request", "req"):
                continue
            if param_name in path_params:
                params[param_name] = path_params[param_name]
                continue

            annotation = hints.get(param_name, inspect.Parameter.empty)
            value = body.get(param_name)

            if value is None:
                if param.default is inspect.Parameter.empty:
                    errors[param_name] = "required field missing"
                    continue
                params[param_name] = param.default
                continue

            try:
                params[param_name] = _coerce(value, annotation)
            except ValueError as e:
                errors[param_name] = str(e)

        if errors:
            return Response.json({"errors": errors}, status=422)

        if inspect.iscoroutinefunction(fn):
            return await fn(request, **params)
        return fn(request, **params)

    return wrapper