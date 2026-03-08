import mimetypes
import os

from .wrappers import Response

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


def serve_static(path: str, static_dir: str, url_prefix: str = "/static") -> Response | None:
    """
    Attempt to serve a static file for the given request path.
    Returns a Response if the file exists, otherwise None.
    """
    if not path.startswith(url_prefix):
        return None

    rel = path[len(url_prefix):].lstrip("/")

    static_dir = os.path.realpath(static_dir)
    file_path = os.path.realpath(os.path.join(static_dir, rel))

    if not file_path.startswith(static_dir):
        return Response(body="403 Forbidden", status=403)

    if not os.path.isfile(file_path):
        return None

    with open(file_path, "rb") as f:
        content = f.read()

    mime, _ = mimetypes.guess_type(file_path)
    content_type = mime or "application/octet-stream"

    return Response(body=content, status=200, content_type=content_type)