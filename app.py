import asyncio
import piu
from piu import (
    PIU, Blueprint, Request, Response,
    SessionMiddleware, CSRFMiddleware,
    RateLimitMiddleware, rate_limit,
    require_auth, login_user, logout_user, current_user,
    Plugin, BackgroundTasks, WebSocket,
)

app = PIU()

app.config.from_env_file(".env")
app.config.load_env()

if not app.config.get("SECRET_KEY"):
    app.config.set("SECRET_KEY", "dev-secret")

app.middleware.use(RateLimitMiddleware(limit=100, window=60))
app.middleware.use(SessionMiddleware(
    secret_key=app.config.get("SECRET_KEY", "dev-secret"),
    max_age=3600,
))
app.middleware.use(CSRFMiddleware(exempt_paths=["/api/"]))

def logger(request: Request, next):
    print(f"[LOG] {request.method} {request.path}")
    return next(request)

app.middleware.use(logger)

@app.errorhandler(404)
def not_found(request, error):
    return Response(body="<h1>404 — Nothing here 🩲</h1>", status=404)

@app.errorhandler(500)
def server_error(request, error):
    return Response(body=f"<h1>500 — {error}</h1>", status=500)

class HealthPlugin(Plugin):
    name = "health"

    def setup(self, app):
        @app.get("/health")
        def health(request: Request):
            return Response.json({"status": "ok", "version": piu.__version__})

app.register_plugin(HealthPlugin())
app.enable_docs(title="PIU Example API")

async def send_welcome_email(username: str):
    await asyncio.sleep(0.1)
    print(f"[TASK] Welcome email sent to {username}")

def write_audit_log(action: str, path: str):
    print(f"[TASK] Audit: {action} {path}")

@app.get("/")
def index(request: Request):
    return app.render("index.html", version=piu.__version__)

@app.get("/login")
def login_page(request: Request):
    return Response(body=f"""
        <form method="POST" action="/login">
            <input type="hidden" name="_csrf_token" value="{request.csrf_token}">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
    """)

@app.post("/login")
@rate_limit(limit=5, window=60)
def login(request: Request):
    form = request.form()
    username = form.get("username", [None])[0]
    password = form.get("password", [None])[0]
    if username == "alice" and password == "secret":
        login_user(request, {"id": 1, "username": username, "role": "admin"})
        request.background_tasks.add(send_welcome_email, username)
        request.background_tasks.add(write_audit_log, "login", request.path)
        return Response.redirect("/dashboard")
    return Response(body="<h1>Bad credentials</h1>", status=401)

@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return Response.redirect("/login")

@app.get("/dashboard")
@require_auth(redirect_to="/login")
def dashboard(request: Request):
    user = current_user(request)
    return Response(body=f"<h1>Welcome, {user['username']}! 🩲</h1>")

@app.get("/admin")
@require_auth(role="admin", redirect_to="/login")
def admin(request: Request):
    return Response(body="<h1>Admin panel</h1>")

api = Blueprint("api", prefix="/api")

@api.get("/me")
@require_auth(status=401)
def me(request: Request):
    return Response.json(current_user(request))

@api.post("/data")
@rate_limit(limit=10, window=60)
def post_data(request: Request):
    return Response.json({"received": request.json()}, status=201)

app.register(api)

@app.ws("/ws/echo")
async def ws_echo(ws: WebSocket):
    while True:
        msg = await ws.receive_text()
        if msg is None:
            break
        await ws.send_text(f"echo: {msg}")

@app.ws("/ws/chat/<room>")
async def ws_chat(ws: WebSocket, room: str):
    await ws.send_text(f"Joined room: {room}")
    while True:
        msg = await ws.receive_text()
        if msg is None:
            break
        await ws.send_text(f"[{room}] {msg}")

if __name__ == "__main__":
    app.run()