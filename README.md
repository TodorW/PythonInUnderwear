# 🩲 Python In Underwear (PIU)

> A lightweight, Flask-inspired web framework for Python. Sync & async, no fluff.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## What is PIU?

**Python In Underwear** is a minimal web framework built for developers who want Flask-like simplicity with modern Python support — including native `async/await`, both WSGI and ASGI interfaces, and a clean middleware pipeline.

No magic. No bloat. Just the bare essentials, done right.

---

## Features

- **Routing** — Decorator-based URL rules with dynamic path parameters (`/user/<id>`)
- **Request & Response** — Clean wrappers with JSON, form, and redirect support
- **Middleware** — Chainable `next`-style stack, sync and async compatible
- **Templates** — Jinja2 integration with autoescaping out of the box
- **WSGI & ASGI** — Deploy with Gunicorn, uWSGI, Uvicorn, or Hypercorn
- **Dev Server** — Built-in server for local development, zero config

---

## Installation

```bash
# Clone the repo
git clone https://github.com/TodorW/PythonInUnderwear.git
cd PythonInUnderwear

# Install dependencies
pip install jinja2
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

Visit `http://127.0.0.1:5000` and you're live.

---

## Routing

```python
@app.get("/users")           # GET
@app.post("/users")          # POST
@app.put("/users/<id>")      # PUT with path param
@app.patch("/users/<id>")    # PATCH
@app.delete("/users/<id>")   # DELETE

# Or explicitly:
@app.route("/users", methods=["GET", "POST"])
def users(request):
    ...
```

---

## Request

```python
request.method          # "GET", "POST", etc.
request.path            # "/hello/world"
request.headers         # dict of headers
request.query_params    # parsed query string dict
request.body            # raw bytes
request.json()          # parsed JSON body
request.form()          # parsed form body
```

---

## Response

```python
# Plain HTML
return Response(body="<h1>Hello</h1>")

# JSON (auto-serialized)
return Response.json({"key": "value"})

# Custom status
return Response(body="Created", status=201)

# Redirect
return Response.redirect("/new-location")

# Custom headers
return Response(body="OK", headers={"X-Custom": "value"})
```

---

## Middleware

```python
def logger(request, next):
    print(f"{request.method} {request.path}")
    return next(request)

async def auth(request, next):
    if "Authorization" not in request.headers:
        return Response(body="Unauthorized", status=401)
    return await next(request)

app.middleware.use(logger)
app.middleware.use(auth)
```

Middleware runs in registration order. Each function must call `next(request)` to pass control down the chain.

---

## Templates

Requires `jinja2`:

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

## Deployment

**WSGI (Gunicorn)**
```bash
gunicorn "myapp:app.wsgi"
```

**ASGI (Uvicorn)**
```bash
uvicorn myapp:app.asgi
```

---

## Project Structure

```
piu/
├── __init__.py      # Public API & version
├── app.py           # Core application class
├── wrappers.py      # Request & Response
├── routing.py       # Route & Router
├── middleware.py    # MiddlewareStack
├── templating.py    # Jinja2 TemplateEngine
├── serving.py       # Dev server
└── helpers.py       # HTTP status utilities
```

---

## License

MIT — do whatever you want with it.