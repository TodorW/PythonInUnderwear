import inspect
import json
import re
from typing import Callable, get_type_hints


def _python_type_to_json(annotation) -> dict:
    mapping = {
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        str: {"type": "string"},
        bytes: {"type": "string", "format": "binary"},
    }
    return mapping.get(annotation, {"type": "string"})


def _extract_path_params(pattern: str) -> list[dict]:
    params = []
    for name in re.findall(r"\(\?P<(\w+)>", pattern):
        params.append({
            "name": name,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        })
    return params


def _route_pattern_to_openapi(pattern: str) -> str:
    clean = pattern.lstrip("^").rstrip("$")
    clean = re.sub(r"\(\?P<(\w+)>[^)]+\)", r"{\1}", clean)
    return clean


def generate_schema(router, title: str = "PIU API", version: str = "0.1.0",
                    description: str = "") -> dict:
    paths = {}

    for route in router._routes:
        raw = route.regex.pattern
        oapi_path = _route_pattern_to_openapi(raw)
        path_params = _extract_path_params(raw)

        if oapi_path not in paths:
            paths[oapi_path] = {}

        for method in route.methods:
            op: dict = {
                "operationId": f"{method.lower()}_{route.handler.__name__}",
                "summary": route.handler.__name__.replace("_", " ").title(),
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad Request"},
                    "401": {"description": "Unauthorized"},
                    "404": {"description": "Not Found"},
                    "500": {"description": "Internal Server Error"},
                },
            }

            if path_params:
                op["parameters"] = path_params

            try:
                hints = get_type_hints(route.handler)
                hints.pop("return", None)
                hints.pop("request", None)
                query_params = []
                for param_name, annotation in hints.items():
                    if param_name not in [p["name"] for p in path_params]:
                        query_params.append({
                            "name": param_name,
                            "in": "query",
                            "required": False,
                            "schema": _python_type_to_json(annotation),
                        })
                if query_params:
                    op.setdefault("parameters", []).extend(query_params)
            except Exception:
                pass

            if method in ("POST", "PUT", "PATCH"):
                op["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }

            doc = inspect.getdoc(route.handler)
            if doc:
                op["description"] = doc

            paths[oapi_path][method.lower()] = op

    return {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": version,
            "description": description,
        },
        "paths": paths,
    }


SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>{title} — API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui.min.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.min.js"></script>
<script>
  SwaggerUIBundle({{
    url: "/openapi.json",
    dom_id: "#swagger-ui",
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "BaseLayout",
    deepLinking: true,
  }});
</script>
</body>
</html>"""