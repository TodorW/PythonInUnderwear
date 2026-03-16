import argparse
import os
import sys


_APP_TEMPLATE = '''\
import piu
from piu import (
    PIU, Request, Response,
    SessionMiddleware, CSRFMiddleware,
    RateLimitMiddleware,
)

app = PIU()

app.config.from_env_file(".env")
app.config.load_env()

app.middleware.use(RateLimitMiddleware(limit=100, window=60))
app.middleware.use(SessionMiddleware(
    secret_key=app.config.get("SECRET_KEY", "dev-secret"),
    max_age=3600,
))
app.middleware.use(CSRFMiddleware())


@app.errorhandler(404)
def not_found(request, error):
    return Response(body="<h1>404 — Not found</h1>", status=404)


@app.get("/")
def index(request: Request):
    return Response(body="<h1>Hello from PIU 🩲</h1>")


if __name__ == "__main__":
    app.run()
'''

_ENV_TEMPLATE = """\
DEBUG=true
HOST=127.0.0.1
PORT=5000
SECRET_KEY=change-me-in-production
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title }}</title>
</head>
<body>
  <h1>🩲 {{ title }}</h1>
  <p>Your PIU app is running.</p>
</body>
</html>
"""

_GITIGNORE_TEMPLATE = """\
__pycache__/
*.pyc
.env
*.egg-info/
dist/
.venv/
"""

_TEST_TEMPLATE = '''\
from piu.testing import TestClient
from app import app

client = TestClient(app)


def test_index():
    resp = client.get("/")
    assert resp.status == 200
'''


def cmd_new(args):
    name = args.name
    base = os.path.join(os.getcwd(), name)

    if os.path.exists(base):
        print(f"[PIU] Error: directory '{name}' already exists.")
        sys.exit(1)

    dirs = [base, os.path.join(base, "templates"),
            os.path.join(base, "static"), os.path.join(base, "tests")]
    for d in dirs:
        os.makedirs(d)

    files = {
        os.path.join(base, "app.py"): _APP_TEMPLATE,
        os.path.join(base, ".env"): _ENV_TEMPLATE,
        os.path.join(base, "templates", "index.html"): _HTML_TEMPLATE,
        os.path.join(base, ".gitignore"): _GITIGNORE_TEMPLATE,
        os.path.join(base, "tests", "test_app.py"): _TEST_TEMPLATE,
    }
    for path, content in files.items():
        with open(path, "w") as f:
            f.write(content)

    print(f"\n[PIU] 🩲 '{name}' created!\n")
    print(f"  cd {name}")
    print(f"  python app.py\n")


def cmd_run(args):
    if not os.path.isfile("app.py"):
        print("[PIU] Error: no app.py found in the current directory.")
        sys.exit(1)

    sys.path.insert(0, os.getcwd())
    try:
        import importlib
        module = importlib.import_module("app")
    except Exception as e:
        print(f"[PIU] Failed to import app.py: {e}")
        sys.exit(1)

    app = getattr(module, "app", None)
    if app is None:
        print("[PIU] Error: app.py must define an 'app' variable.")
        sys.exit(1)

    if os.path.isfile(".env"):
        app.config.from_env_file(".env")
    app.config.load_env()

    host = args.host or app.config.get("HOST", "127.0.0.1")
    port = args.port or app.config.get("PORT", 5000)
    reload = args.reload or app.config.get("DEBUG", False)

    app.run(host=host, port=int(port), reload=reload)


def main():
    parser = argparse.ArgumentParser(prog="piu", description="🩲 Python In Underwear CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Scaffold a new PIU project")
    p_new.add_argument("name", help="Project name")
    p_new.set_defaults(func=cmd_new)

    p_run = sub.add_parser("run", help="Run the development server")
    p_run.add_argument("--host", default=None)
    p_run.add_argument("--port", default=None, type=int)
    p_run.add_argument("--reload", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()