import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .wrappers import Request


def run_dev_server(app, host: str = "127.0.0.1", port: int = 5000):
    """Start a simple development HTTP server (not for production use)."""

    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            req = Request(
                method=self.command,
                path=parsed.path,
                headers=dict(self.headers),
                body=body,
                query_params=query,
            )

            resp = asyncio.run(app._dispatch(req))

            self.send_response(resp.status)
            self.send_header("Content-Type", resp.content_type)
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.body)

        def do_GET(self): self._handle()
        def do_POST(self): self._handle()
        def do_PUT(self): self._handle()
        def do_DELETE(self): self._handle()
        def do_PATCH(self): self._handle()

        def log_message(self, fmt, *args):
            print(f"[PIU] {self.address_string()} - {fmt % args}")

    print(f"[PIU] 🩲 Dev server running on http://{host}:{port}  (Ctrl+C to stop)")
    HTTPServer((host, port), Handler).serve_forever()