import asyncio
import os
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .wrappers import Request


def run_dev_server(app, host: str = "127.0.0.1", port: int = 5000,
                   reload: bool = False):
    if reload and os.environ.get("PIU_RELOADER_CHILD") != "1":
        _run_with_reload(host, port)
        return
    _serve(app, host, port)


def _make_handler(app, loop):
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

            resp = loop.run_until_complete(app._dispatch(req))
            resp = app._finalize(resp)

            self.send_response(resp.status)
            self.send_header("Content-Type", resp.content_type)
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.body)

        def do_GET(self):    self._handle()
        def do_POST(self):   self._handle()
        def do_PUT(self):    self._handle()
        def do_DELETE(self): self._handle()
        def do_PATCH(self):  self._handle()

        def log_message(self, fmt, *args):
            print(f"[PIU] {self.address_string()} - {fmt % args}")

    return Handler


def _serve(app, host: str, port: int):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    Handler = _make_handler(app, loop)
    server = HTTPServer((host, port), Handler)
    print(f"[PIU] 🩲 Dev server running on http://{host}:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[PIU] Shutting down. Bye 🩲")
    finally:
        server.server_close()
        loop.close()


def _run_with_reload(host: str, port: int):
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("[PIU] Hot reload requires watchdog: pip install watchdog")
        sys.exit(1)

    env = os.environ.copy()
    env["PIU_RELOADER_CHILD"] = "1"

    process: list[subprocess.Popen] = [None]

    def start():
        process[0] = subprocess.Popen([sys.executable] + sys.argv, env=env)

    def restart():
        if process[0] and process[0].poll() is None:
            print("[PIU] 🔄 Change detected — restarting...")
            process[0].terminate()
            process[0].wait()
        start()

    class ChangeHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                restart()

    start()

    observer = Observer()
    observer.schedule(ChangeHandler(), path=".", recursive=True)
    observer.start()
    print("[PIU] 👀 Watching for changes (hot reload active)...")

    try:
        while True:
            time.sleep(1)
            if process[0] and process[0].poll() is not None:
                start()
    except KeyboardInterrupt:
        print("\n[PIU] Shutting down. Bye 🩲")
        observer.stop()
        if process[0] and process[0].poll() is None:
            process[0].terminate()
    finally:
        observer.join()