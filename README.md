# 🩲 Python In Underwear (PIU)

> A lightweight, Flask-inspired web framework for Python. Sync & async, no fluff.

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## What is PIU?

**Python In Underwear** is a minimal web framework built for developers who want Flask-like simplicity with modern Python support — native `async/await`, WSGI and ASGI interfaces, sessions, auth, rate limiting, WebSockets, OpenAPI docs, and more.

No magic. No bloat. Zero required dependencies.

---

## Features

- **Routing** — Decorator-based URL rules with dynamic path parameters (`/user/<id>`)
- **Blueprints** — Group routes into reusable modules with URL prefixes
- **Request & Response** — Clean wrappers with JSON, form, cookie, and redirect support
- **Middleware** — Chainable `next`-style stack, sync and async compatible
- **Sessions** — HMAC-signed cookie-based sessions, no server-side storage needed
- **CSRF Protection** — Token-based CSRF middleware with form and header support
- **Rate Limiting** — Global and per-route sliding window rate limiting
- **Auth** — `@require_auth` decorator with role-based access control
- **Templates** — Jinja2 integration with autoescaping out of the box
- **Static Files** — Automatic static file serving from a configurable directory
- **Config** — Load config from dict, `.env`, YAML, or environment variables
- **Hot Reload** — File watcher restarts the server on code changes
- **Test Client** — In-process HTTP client with cookie jar, no server needed
- **Plugins** — `app.register_plugin()` API for modular extensions
- **Background Tasks** — Fire-and-forget async/sync tasks from within handlers
- **WebSockets** — `@app.ws()` decorator over the ASGI interface
- **OpenAPI / Swagger** — Auto-generated docs served at `/docs`
- **WSGI & ASGI** — Deploy with Gunicorn, uWSGI, Uvicorn, or Hypercorn
- **CLI** — `piu new` and `piu run` commands

---

## Installation

```bash
git clone https://github.com/TodorW/PythonInUnderwear.git
cd PythonInUnderwear
pip install -e ".[full]"
```

Or install extras individually:

```bash
pip install -e ".[templates]"   # jinja2
pip install -e ".[dev]"         # jinja2 + watchdog + pytest
pip install -e ".[full]"        # everything
```

---

## Quickstart

```python
from piu import PIU, Request, Response

app = PIU()

@app.get("/")
def index(request: Request):
    return Response(body="<h1>Hello from PIU 🩲</h1>")

@app.get("/hello/<name>")
async def hello(request: Request, name: str):
    return Response.json({"message": f"Hello, {name}!"})

@app.post("/echo")
def echo(request: Request):
    return Response.json({"you_sent": request.json()})

if __name__ == "__main__":
    app.run()
```

---

## CLI

```bash
piu new myapp       # scaffold a new project
piu run             # run the dev server
piu run --reload    # run with hot reload
```

If `piu` isn't on PATH, use:

```bash
python -m piu new myapp
python -m piu run --reload
```

---

## Routing

```python
@app.get("/users")
@app.post("/users")
@app.put("/users/<id>")
@app.patch("/users/<id>")
@app.delete("/users/<id>")

# Or explicitly:
@app.route("/users", methods=["GET", "POST"])
def users(request):
    ...
```

---

## Blueprints

```python
from piu import Blueprint

api = Blueprint("api", prefix="/api")

@api.get("/users")
def users(request):
    return Response.json([{"id": 1}])

app.register(api)
# or override prefix:
app.register(api, prefix="/v2")
```

---

## Request

```python
request.method            # "GET", "POST", etc.
request.path              # "/hello/world"
request.headers           # dict of headers
request.query_params      # parsed query string dict
request.body              # raw bytes
request.cookies           # dict of incoming cookies
request.session           # session dict (requires SessionMiddleware)
request.csrf_token        # current CSRF token (requires CSRFMiddleware)
request.background_tasks  # BackgroundTasks instance
request.json()            # parsed JSON body
request.form()            # parsed form body
```

---

## Response

```python
return Response(body="<h1>Hello</h1>")
return Response.json({"key": "value"})
return Response(body="Created", status=201)
return Response.redirect("/new-location")
return Response(body="OK", headers={"X-Custom": "value"})

# Cookies
resp = Response(body="ok")
resp.set_cookie("token", "abc123", max_age=3600, httponly=True)
resp.delete_cookie("token")
```

---

## Middleware

```python
def logger(request, next):
    print(f"{request.method} {request.path}")
    return next(request)

async def auth_check(request, next):
    if "Authorization" not in request.headers:
        return Response(body="Unauthorized", status=401)
    return await next(request)

app.middleware.use(logger)
app.middleware.use(auth_check)
```

---

## Sessions

```python
from piu import SessionMiddleware

app.middleware.use(SessionMiddleware(secret_key="your-secret", max_age=3600))

@app.get("/set")
def set_session(request):
    request.session["user"] = "alice"
    return Response(body="ok")

@app.get("/get")
def get_session(request):
    return Response.json({"user": request.session.get("user")})
```

---

## CSRF Protection

```python
from piu import CSRFMiddleware

app.middleware.use(CSRFMiddleware(exempt_paths=["/api/"]))

# In your form template:
# <input type="hidden" name="_csrf_token" value="{{ request.csrf_token }}">

# Or in JS via header:
# X-CSRF-Token: <token>
```

---

## Rate Limiting

```python
from piu import RateLimitMiddleware, rate_limit

# Global: 100 req/min per IP
app.middleware.use(RateLimitMiddleware(limit=100, window=60))

# Per-route
@app.post("/login")
@rate_limit(limit=5, window=60)
def login(request):
    ...
```

---

## Auth

```python
from piu import require_auth, login_user, logout_user, current_user

@app.post("/login")
def login(request):
    login_user(request, {"id": 1, "role": "admin"})
    return Response.redirect("/dashboard")

@app.get("/dashboard")
@require_auth(redirect_to="/login")
def dashboard(request):
    user = current_user(request)
    return Response(body=f"Hello {user['id']}")

@app.get("/admin")
@require_auth(role="admin", redirect_to="/login")
def admin(request):
    ...

@app.get("/logout")
def logout(request):
    logout_user(request)
    return Response.redirect("/login")
```

---

## Templates

```python
app = PIU(template_dir="templates")

@app.get("/page")
def page(request):
    return app.render("index.html", title="Home", user="Alice")
```

```html
<!-- templates/index.html -->
<h1>{{ title }}</h1>
<p>Welcome, {{ user }}!</p>
```

---

## Config

```python
app.config.from_env_file(".env")       # load from .env
app.config.from_yaml("config.yaml")    # load from YAML
app.config.from_dict({"DEBUG": True})  # load from dict
app.config.load_env(prefix="PIU_")     # load PIU_* env vars

app.config["SECRET_KEY"] = "abc"
val = app.config.get("PORT", 5000)
```

---

## Background Tasks

```python
async def send_email(to: str):
    ...

@app.post("/register")
def register(request):
    request.background_tasks.add(send_email, "user@example.com")
    return Response(body="registered", status=201)
```

---

## Plugins

```python
from piu import Plugin

class HealthPlugin(Plugin):
    name = "health"

    def setup(self, app):
        @app.get("/health")
        def health(req):
            return Response.json({"status": "ok"})

app.register_plugin(HealthPlugin())
```

---

## WebSockets

Requires Uvicorn (`pip install uvicorn`):

```python
from piu import WebSocket

@app.ws("/ws/echo")
async def echo(ws: WebSocket):
    while True:
        msg = await ws.receive_text()
        if msg is None:
            break
        await ws.send_text(f"echo: {msg}")
```

```bash
uvicorn app:app
```

---

## OpenAPI / Swagger

```python
app.enable_docs(title="My API")
# Swagger UI → http://127.0.0.1:5000/docs
# Raw schema → http://127.0.0.1:5000/openapi.json
```

---

## Testing

```python
from piu.testing import TestClient
from app import app

client = TestClient(app)

def test_index():
    resp = client.get("/")
    assert resp.status == 200

def test_json():
    resp = client.post("/echo", json={"hello": "world"})
    assert resp.json() == {"hello": "world"}
```

```bash
pytest tests/ -v
```

---

## Deployment

**WSGI (Gunicorn)**
```bash
gunicorn "app:app.wsgi"
```

**ASGI (Uvicorn)**
```bash
uvicorn app:app
```

---

## Project Structure

```
piu/
├── __init__.py      # Public API & version
├── __main__.py      # python -m piu entry point
├── app.py           # Core application class
├── auth.py          # @require_auth, login/logout helpers
├── cli.py           # CLI commands
├── config.py        # Config management
├── csrf.py          # CSRF middleware
├── helpers.py       # HTTP status utilities
├── middleware.py    # MiddlewareStack
├── openapi.py       # OpenAPI schema + Swagger UI
├── plugins.py       # Plugin base class
├── ratelimit.py     # Rate limiting middleware & decorator
├── routing.py       # Route, Router & Blueprint
├── serving.py       # Dev server & hot reload
├── sessions.py      # Session middleware
├── static.py        # Static file serving
├── tasks.py         # Background tasks
├── templating.py    # Jinja2 TemplateEngine
├── testing.py       # TestClient
├── websocket.py     # WebSocket support
└── wrappers.py      # Request & Response
```

---

## License

MIT — do whatever you want with it.