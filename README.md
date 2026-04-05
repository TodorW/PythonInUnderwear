# 🩲 Python In Underwear — Documentation

> Version 0.6.0 | Python 3.10+ | MIT License

---

## Table of Contents

1. [What is PIU?](#what-is-piu)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [CLI](#cli)
5. [Application](#application)
6. [Routing](#routing)
7. [Request](#request)
8. [Response](#response)
9. [Middleware](#middleware)
10. [Sessions](#sessions)
11. [Authentication](#authentication)
12. [CSRF Protection](#csrf-protection)
13. [Rate Limiting](#rate-limiting)
14. [CORS](#cors)
15. [Request Validation](#request-validation)
16. [File Uploads](#file-uploads)
17. [Response Caching](#response-caching)
18. [Static Files](#static-files)
19. [Templates](#templates)
20. [Blueprints](#blueprints)
21. [Plugins](#plugins)
22. [Background Tasks](#background-tasks)
23. [WebSockets](#websockets)
24. [Database](#database)
25. [Config](#config)
26. [Logging](#logging)
27. [OpenAPI / Swagger](#openapi--swagger)
28. [Testing](#testing)
29. [Deployment](#deployment)
30. [Error Handling](#error-handling)

---

## What is PIU?

**Python In Underwear (PIU)** is a lightweight, Flask-inspired web framework for Python 3.10+. It supports both sync and async route handlers, has zero required dependencies, and ships with a complete set of production-ready features out of the box — sessions, auth, CSRF, rate limiting, CORS, WebSockets, OpenAPI docs, database integration, and more.

PIU is built for developers who want Flask-like simplicity without the need to install a dozen extensions just to build a real app.

---

## Installation

```bash
# From PyPI
pip install python-in-underwear

# With optional dependencies
pip install "python-in-underwear[templates]"    # Jinja2 templates
pip install "python-in-underwear[dev]"          # Jinja2 + watchdog + pytest
pip install "python-in-underwear[db]"           # SQLAlchemy + aiosqlite (SQLite)
pip install "python-in-underwear[db-pg]"        # SQLAlchemy + asyncpg (PostgreSQL)
pip install "python-in-underwear[db-mysql]"     # SQLAlchemy + aiomysql (MySQL)
pip install "python-in-underwear[full]"         # Everything
```

---

## Quick Start

```python
from piu import PIU, Request, Response

app = PIU()

@app.get("/")
def index(request: Request):
    return Response(body="<h1>Hello from PIU 🩲</h1>")

@app.get("/hello/<name>")
async def hello(request: Request, name: str):
    return Response.json({"message": f"Hello, {name}!"})

if __name__ == "__main__":
    app.run()
```

```bash
python app.py
# Server running at http://127.0.0.1:5000
```

---

## CLI

PIU ships with a command line tool for scaffolding and running projects.

### `piu new <name>`
Scaffold a new PIU project with a recommended structure.

```bash
piu new myapp
cd myapp
python app.py
```

Creates:
```
myapp/
├── app.py
├── .env
├── .env.example
├── .gitignore
├── templates/
│   └── index.html
├── static/
└── tests/
    └── test_app.py
```

### `piu run`
Run the development server using `app.py` in the current directory.

```bash
piu run
piu run --host 0.0.0.0 --port 8000
piu run --reload       # hot reload on file changes
```

### `piu routes`
Print all registered HTTP and WebSocket routes.

```bash
piu routes
```

Output:
```
  METHOD       PATH                                     HANDLER
  ──────────────────────────────────────────────────────────────────────
  GET          /                                        index
  GET          /users/<id>                              get_user
  POST         /users                                   create_user

  WS           PATH                                     HANDLER
  ──────────────────────────────────────────────────────────────────────
  WS           /ws/chat                                 chat
```

> If `piu` isn't on PATH, use `python -m piu <command>` instead.

---

## Application

```python
from piu import PIU

app = PIU(
    template_dir="templates",   # Jinja2 templates directory
    static_dir="static",        # Static files directory
    static_url="/static",       # URL prefix for static files
    config={"DEBUG": True},     # Initial config values
)
```

### Running the server

```python
app.run()                                # Uses config HOST/PORT/DEBUG
app.run(host="0.0.0.0", port=8000)
app.run(reload=True)                     # Hot reload
```

### ASGI / WSGI

```python
# Uvicorn (ASGI) — supports async + WebSockets
uvicorn app:app

# Gunicorn (WSGI) — sync only
gunicorn "app:app.wsgi"
```

---

## Routing

```python
@app.get("/users")
@app.post("/users")
@app.put("/users/<id>")
@app.patch("/users/<id>")
@app.delete("/users/<id>")

# Custom methods
@app.route("/users", methods=["GET", "POST"])
def users(request):
    ...
```

### Dynamic path parameters

```python
@app.get("/users/<id>")
def get_user(request: Request, id: str):
    return Response.json({"id": id})

@app.get("/posts/<post_id>/comments/<comment_id>")
def get_comment(request: Request, post_id: str, comment_id: str):
    ...
```

---

## Request

```python
request.method           # "GET", "POST", etc.
request.path             # "/users/42"
request.headers          # dict of request headers
request.query_params     # {"q": ["search term"]}  (always lists)
request.body             # raw bytes
request.cookies          # {"session": "abc123"}
request.session          # session dict (requires SessionMiddleware)
request.csrf_token       # current CSRF token string
request.files            # {"avatar": UploadedFile(...)}
request.form_fields      # {"username": "alice"}
request.background_tasks # BackgroundTasks instance

# Parsed body helpers
request.json()           # parse JSON body → dict
request.form()           # parse form body → dict of lists
```

### Query params

```python
@app.get("/search")
def search(request: Request):
    q = request.query_params.get("q", [None])[0]
    page = int(request.query_params.get("page", [1])[0])
    return Response.json({"q": q, "page": page})
```

---

## Response

```python
# HTML
return Response(body="<h1>Hello</h1>")

# JSON — dict/list auto-serialized
return Response.json({"key": "value"})
return Response.json({"error": "not found"}, status=404)

# Custom status
return Response(body="Created", status=201)

# Redirect
return Response.redirect("/dashboard")
return Response.redirect("/login", status=301)

# Custom headers
return Response(body="ok", headers={"X-Custom": "value"})

# Cookies
resp = Response(body="ok")
resp.set_cookie("token", "abc", max_age=3600, httponly=True, secure=False)
resp.delete_cookie("token")
return resp
```

---

## Middleware

Middleware runs in registration order. Each function receives the request and a `next` callable to pass control down the chain.

```python
# Sync middleware
def logger(request: Request, next):
    print(f"{request.method} {request.path}")
    return next(request)

# Async middleware
async def auth_check(request: Request, next):
    if not request.headers.get("Authorization"):
        return Response(body="Unauthorized", status=401)
    return await next(request)

app.middleware.use(logger)
app.middleware.use(auth_check)
```

### Recommended middleware order

```python
app.middleware.use(LoggingMiddleware())
app.middleware.use(RateLimitMiddleware(limit=100, window=60))
app.middleware.use(SessionMiddleware(secret_key="your-secret"))
app.middleware.use(CORSMiddleware(allow_origins=["*"]))
app.middleware.use(CSRFMiddleware(exempt_paths=["/api/"]))
```

---

## Sessions

Cookie-based sessions signed with HMAC-SHA256. No server-side storage required.

```python
from piu import SessionMiddleware

app.middleware.use(SessionMiddleware(
    secret_key="your-secret-key",   # required
    max_age=3600,                   # seconds (default: 86400)
    httponly=True,
    secure=False,                   # set True in production with HTTPS
    samesite="Lax",
))
```

```python
@app.get("/set")
def set_session(request: Request):
    request.session["user_id"] = 42
    request.session["role"] = "admin"
    return Response(body="ok")

@app.get("/get")
def get_session(request: Request):
    user_id = request.session.get("user_id")
    return Response.json({"user_id": user_id})

@app.get("/clear")
def clear_session(request: Request):
    request.session.clear()
    return Response(body="ok")
```

---

## Authentication

```python
from piu import require_auth, login_user, logout_user, current_user, is_authenticated
```

### Logging in and out

```python
@app.post("/login")
def login(request: Request):
    # Validate credentials here
    login_user(request, {"id": 1, "username": "alice", "role": "admin"})
    return Response.redirect("/dashboard")

@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return Response.redirect("/login")
```

### Protecting routes

```python
# Redirect to /login if not authenticated
@app.get("/dashboard")
@require_auth(redirect_to="/login")
def dashboard(request: Request):
    user = current_user(request)
    return Response(body=f"Hello {user['username']}")

# Return 401 if not authenticated (for API routes)
@app.get("/api/me")
@require_auth(status=401)
def me(request: Request):
    return Response.json(current_user(request))

# Require a specific role
@app.get("/admin")
@require_auth(role="admin", redirect_to="/login")
def admin(request: Request):
    return Response(body="Admin panel")
```

### Helpers

```python
current_user(request)       # → dict or None
is_authenticated(request)   # → bool
```

---

## CSRF Protection

```python
from piu import CSRFMiddleware

app.middleware.use(CSRFMiddleware(
    exempt_paths=["/api/", "/webhooks/"]  # skip CSRF for these prefixes
))
```

CSRF tokens are validated on `POST`, `PUT`, `PATCH`, and `DELETE` requests. Pass the token via:

**HTML form:**
```html
<form method="POST" action="/submit">
    <input type="hidden" name="_csrf_token" value="{{ request.csrf_token }}">
    ...
</form>
```

**JavaScript / AJAX:**
```javascript
fetch("/api/data", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(data)
})
```

---

## Rate Limiting

```python
from piu import RateLimitMiddleware, rate_limit
```

### Global rate limiting

```python
# 100 requests per 60 seconds per IP, applied to every route
app.middleware.use(RateLimitMiddleware(limit=100, window=60))
```

### Per-route rate limiting

```python
@app.post("/login")
@rate_limit(limit=5, window=60)   # 5 attempts per minute
def login(request: Request):
    ...
```

Returns `429 Too Many Requests` with a `Retry-After` header when the limit is exceeded.

---

## CORS

```python
from piu.cors import CORSMiddleware

app.middleware.use(CORSMiddleware(
    allow_origins=["https://myapp.com", "https://app.myapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=600,
))

# Allow all origins
app.middleware.use(CORSMiddleware(allow_origins=["*"]))
```

Preflight `OPTIONS` requests are handled automatically.

---

## Request Validation

```python
from piu import validate

@app.post("/users")
@validate
def create_user(request: Request, name: str, age: int, email: str):
    return Response.json({"name": name, "age": age, "email": email}, status=201)
```

PIU parses the JSON body and injects fields as kwargs, coercing types automatically. Returns `422 Unprocessable Entity` with field-level errors if validation fails:

```json
{
    "errors": {
        "age": "Expected int, got str",
        "email": "required field missing"
    }
}
```

Parameters with default values are optional:

```python
@app.post("/search")
@validate
def search(request: Request, q: str, page: int = 1, limit: int = 20):
    ...
```

---

## File Uploads

File uploads are automatically parsed from `multipart/form-data` requests and attached to the request object.

```python
@app.post("/upload")
def upload(request: Request):
    file = request.files.get("avatar")
    if not file:
        return Response(body="No file", status=400)

    path = file.save("uploads/")
    return Response.json({
        "filename": file.filename,
        "size": file.size,
        "content_type": file.content_type,
        "saved_to": path,
    })
```

```python
file.filename      # original filename
file.content_type  # e.g. "image/jpeg"
file.data          # raw bytes
file.size          # size in bytes
file.save(dir)     # save to directory, returns path
file.save(dir, filename="custom.jpg")  # save with custom name
```

Form fields (non-file inputs) are available on `request.form_fields`:

```python
username = request.form_fields.get("username")
```

---

## Response Caching

```python
from piu import cache, clear_cache

@app.get("/expensive")
@cache(ttl=60)   # cache for 60 seconds
def expensive(request: Request):
    result = do_expensive_computation()
    return Response.json(result)
```

Cached responses include an `X-Cache: HIT` or `X-Cache: MISS` header.

### Custom cache key

```python
@app.get("/user/<id>")
@cache(ttl=120, key_func=lambda req, **kw: f"user:{kw.get('id')}")
def get_user(request: Request, id: str):
    ...
```

### Clearing the cache

```python
clear_cache()           # clear all cached responses
clear_cache("/users")   # clear a specific key
```

---

## Static Files

Static files are served automatically from the configured directory.

```python
app = PIU(static_dir="static", static_url="/static")
```

A file at `static/style.css` is served at `/static/style.css`. Directory traversal attacks are blocked automatically.

---

## Templates

Requires `jinja2`:

```python
app = PIU(template_dir="templates")

@app.get("/page")
def page(request: Request):
    return app.render("index.html", title="Home", user="Alice")
```

```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>Welcome, {{ user }}!</h1>
</body>
</html>
```

Autoescaping is enabled for `.html` and `.xml` files.

### Rendering from a string

```python
from piu import TemplateEngine

engine = TemplateEngine("templates")
html = engine.render_string("<h1>{{ title }}</h1>", title="Hello")
```

---

## Blueprints

Group related routes into reusable modules.

```python
from piu import Blueprint

api = Blueprint("api", prefix="/api")

@api.get("/users")
def list_users(request: Request):
    return Response.json([{"id": 1, "name": "Alice"}])

@api.post("/users")
def create_user(request: Request):
    data = request.json()
    return Response.json(data, status=201)

@api.get("/users/<id>")
def get_user(request: Request, id: str):
    return Response.json({"id": id})

# Register on the app
app.register(api)

# Override the prefix at registration time
app.register(api, prefix="/v2")
```

Blueprints support all HTTP method decorators: `get`, `post`, `put`, `patch`, `delete`, `route`.

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

        app.config.set("HEALTH_ENABLED", True)

app.register_plugin(HealthPlugin())
```

Plugins have full access to the app instance during `setup()` — they can add routes, register middleware, and modify config.

---

## Background Tasks

Fire-and-forget tasks that run after the response is sent to the client.

```python
async def send_welcome_email(email: str):
    await some_email_client.send(email, "Welcome!")

def write_audit_log(user_id: int, action: str):
    with open("audit.log", "a") as f:
        f.write(f"{user_id} {action}\n")

@app.post("/register")
def register(request: Request):
    data = request.json()
    # Do registration logic...

    # These run after the response is returned
    request.background_tasks.add(send_welcome_email, data["email"])
    request.background_tasks.add(write_audit_log, data["id"], "register")

    return Response.json({"status": "registered"}, status=201)
```

Both sync and async functions are supported.

---

## WebSockets

Requires Uvicorn (`pip install uvicorn`).

```python
from piu import WebSocket

@app.ws("/ws/echo")
async def echo(ws: WebSocket):
    while True:
        msg = await ws.receive_text()
        if msg is None:   # client disconnected
            break
        await ws.send_text(f"echo: {msg}")

@app.ws("/ws/chat/<room>")
async def chat(ws: WebSocket, room: str):
    await ws.send_text(f"Joined room: {room}")
    while True:
        msg = await ws.receive_text()
        if msg is None:
            break
        await ws.send_text(f"[{room}] {msg}")
```

```python
ws.path             # request path
ws.headers          # dict of headers
ws.query_params     # raw query string

await ws.send_text(data: str)
await ws.send_bytes(data: bytes)
await ws.receive_text() → str | None
await ws.receive_bytes() → bytes | None
await ws.close(code=1000)
```

Run with Uvicorn:

```bash
uvicorn app:app
```

---

## Database

Requires SQLAlchemy (`pip install "python-in-underwear[db]"`).

```python
from piu.database import Database, Model
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

db = Database("sqlite+aiosqlite:///app.db")

class User(Model):
    __tablename__ = "users"
    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)
```

### Creating tables

```python
import asyncio
asyncio.run(db.create_tables())
```

### Querying

```python
from sqlalchemy import select

@app.get("/users")
async def list_users(request: Request):
    async with db.session() as s:
        result = await s.execute(select(User))
        users = result.scalars().all()
        return Response.json([{"id": u.id, "name": u.name} for u in users])

@app.post("/users")
async def create_user(request: Request):
    data = request.json()
    async with db.session() as s:
        user = User(name=data["name"], email=data["email"])
        s.add(user)
    return Response.json({"status": "created"}, status=201)
```

The session context manager auto-commits on success and auto-rolls back on error.

### Connection strings

```python
# SQLite
db = Database("sqlite+aiosqlite:///app.db")

# PostgreSQL
db = Database("postgresql+asyncpg://user:password@localhost/dbname")

# MySQL
db = Database("mysql+aiomysql://user:password@localhost/dbname")
```

---

## Config

```python
app = PIU(config={"DEBUG": True, "PORT": 8000})

# Load from .env file
app.config.from_env_file(".env")

# Load from YAML (requires pyyaml)
app.config.from_yaml("config.yaml")

# Load PIU_* prefixed environment variables
app.config.load_env(prefix="PIU_")

# Get / set values
app.config["SECRET_KEY"] = "abc"
val = app.config.get("PORT", 5000)
all_config = app.config.all()
```

### Default config keys

| Key | Default | Description |
|-----|---------|-------------|
| `DEBUG` | `False` | Enables debug mode and hot reload |
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `5000` | Server port |
| `SECRET_KEY` | `""` | Used for session signing |
| `TEMPLATE_DIR` | `templates` | Jinja2 template directory |
| `STATIC_DIR` | `static` | Static files directory |
| `STATIC_URL` | `/static` | Static files URL prefix |

### `.env` file format

```env
DEBUG=true
HOST=127.0.0.1
PORT=5000
SECRET_KEY=your-secret-key
VERSION=1.0.0
```

Values are auto-cast to `int`, `float`, or `bool`.

---

## Logging

```python
from piu.logging import LoggingMiddleware, get_logger

# Add request/response logging middleware
app.middleware.use(LoggingMiddleware())

# With header logging
app.middleware.use(LoggingMiddleware(log_headers=True))
```

Output:
```
10:42:31 INFO     GET     /users                                   200  4.2ms
10:42:31 INFO     POST    /users                                   201  12.1ms
10:42:31 WARNING  GET     /missing                                 404  0.8ms
```

### Custom logger

```python
from piu.logging import get_logger

logger = get_logger("myapp")
logger.info("App started")
logger.warning("Something looks off")
logger.error("Something broke")
```

---

## OpenAPI / Swagger

```python
app.enable_docs(title="My API", path="/docs")
```

- Swagger UI → `http://127.0.0.1:5000/docs`
- Raw OpenAPI JSON → `http://127.0.0.1:5000/openapi.json`

PIU automatically introspects route paths, HTTP methods, path parameters, and docstrings to build the schema.

```python
@app.get("/users/<id>")
def get_user(request: Request, id: str):
    """Get a single user by ID."""
    return Response.json({"id": id})
```

---

## Testing

```python
from piu import PIUTestClient
from app import app

client = PIUTestClient(app)
```

No server needed — requests run in-process. The test client has a built-in cookie jar that persists across requests, so sessions work naturally in tests.

```python
# HTTP methods
resp = client.get("/users")
resp = client.post("/users", json={"name": "Alice"})
resp = client.put("/users/1", json={"name": "Bob"})
resp = client.patch("/users/1", json={"name": "Charlie"})
resp = client.delete("/users/1")
resp = client.options("/users")

# With query params
resp = client.get("/search", query={"q": "alice"})

# With headers
resp = client.get("/protected", headers={"Authorization": "Bearer token"})

# With form data
resp = client.post("/form", data={"username": "alice", "password": "secret"})

# Response
resp.status          # 200
resp.headers         # {"Content-Type": "application/json", ...}
resp.content_type    # "application/json"
resp.body            # b'{"id": 1}'
resp.text()          # '{"id": 1}'
resp.json()          # {"id": 1}
```

### Example test file

```python
import pytest
from piu import PIUTestClient, PIU, Request, Response, SessionMiddleware, CSRFMiddleware

def make_app():
    app = PIU()
    app.middleware.use(SessionMiddleware(secret_key="test"))
    app.middleware.use(CSRFMiddleware(exempt_paths=["/"]))
    return app

def test_index():
    app = make_app()

    @app.get("/")
    def index(req):
        return Response(body="hello")

    resp = PIUTestClient(app).get("/")
    assert resp.status == 200
    assert resp.text() == "hello"
```

Run tests:

```bash
pytest tests/ -v
python -m pytest tests/ -v   # if pytest isn't on PATH
```

---

## Deployment

### Development

```bash
python app.py
# or
piu run --reload
```

### Production with Uvicorn (recommended)

```bash
pip install uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production with Gunicorn (sync only, no WebSockets)

```bash
pip install gunicorn
gunicorn "app:app.wsgi" --bind 0.0.0.0:8000 --workers 4
```

### Production checklist

- Set `DEBUG=false` in `.env`
- Set a strong `SECRET_KEY`
- Use HTTPS (set `secure=True` on cookies)
- Use `CORSMiddleware` with specific origins, not `"*"`
- Use environment variables for secrets, never commit `.env`
- Run behind a reverse proxy (Nginx, Caddy)

---

## Error Handling

```python
@app.errorhandler(404)
def not_found(request: Request, error):
    return Response(body="<h1>404 — Page not found</h1>", status=404)

@app.errorhandler(500)
def server_error(request: Request, error):
    return Response(body=f"<h1>500 — Server error</h1>", status=500)
```

In debug mode (`DEBUG=true`), unhandled exceptions show a full traceback in the browser automatically.

---

## Project Structure

```
piu/
├── __init__.py      # Public API & version
├── __main__.py      # python -m piu entry point
├── app.py           # Core PIU application class
├── auth.py          # @require_auth, login/logout helpers
├── cache.py         # @cache decorator
├── cli.py           # CLI commands
├── config.py        # Config management
├── cors.py          # CORS middleware
├── csrf.py          # CSRF middleware
├── database.py      # SQLAlchemy async integration
├── helpers.py       # HTTP status utilities
├── logging.py       # Logging middleware & logger
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
├── testing.py       # PIUTestClient
├── uploads.py       # File upload parsing
├── validation.py    # @validate decorator
├── websocket.py     # WebSocket support
└── wrappers.py      # Request & Response
```

---

## License

MIT — do whatever you want with it.

---

*Python In Underwear — because sometimes you just want the bare essentials.* 🩲
