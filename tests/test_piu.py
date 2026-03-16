import asyncio
import pytest
from piu import (
    PIU, Request, Response, Blueprint,
    SessionMiddleware, CSRFMiddleware,
    RateLimitMiddleware, rate_limit,
    require_auth, login_user, logout_user, current_user,
    Plugin,
)
from piu.testing import TestClient


def make_app():
    app = PIU()
    app.middleware.use(SessionMiddleware(secret_key="test-secret"))
    app.middleware.use(CSRFMiddleware(exempt_paths=["/"]))
    return app

def test_basic_get():
    app = make_app()

    @app.get("/")
    def index(req):
        return Response(body="hello")

    client = TestClient(app)
    resp = client.get("/")
    assert resp.status == 200
    assert resp.text() == "hello"


def test_404():
    app = make_app()
    client = TestClient(app)
    resp = client.get("/nope")
    assert resp.status == 404


def test_path_param():
    app = make_app()

    @app.get("/hello/<name>")
    def hello(req, name):
        return Response.json({"name": name})

    client = TestClient(app)
    resp = client.get("/hello/world")
    assert resp.status == 200
    assert resp.json()["name"] == "world"


def test_post_json():
    app = make_app()

    @app.post("/echo")
    def echo(req):
        return Response.json(req.json())

    client = TestClient(app)
    resp = client.post("/echo", json={"key": "val"})
    assert resp.status == 200
    assert resp.json() == {"key": "val"}


def test_methods():
    app = make_app()

    @app.put("/item/<id>")
    def put_item(req, id):
        return Response.json({"id": id, "method": "PUT"})

    @app.delete("/item/<id>")
    def del_item(req, id):
        return Response(body="deleted", status=200)

    client = TestClient(app)
    assert client.put("/item/42").json()["method"] == "PUT"
    assert client.delete("/item/42").status == 200


def test_custom_error_handler():
    app = make_app()

    @app.errorhandler(404)
    def not_found(req, err):
        return Response(body="custom 404", status=404)

    client = TestClient(app)
    resp = client.get("/missing")
    assert resp.status == 404
    assert resp.text() == "custom 404"

def test_blueprint():
    app = make_app()
    bp = Blueprint("api", prefix="/api")

    @bp.get("/ping")
    def ping(req):
        return Response.json({"pong": True})

    app.register(bp)
    client = TestClient(app)
    resp = client.get("/api/ping")
    assert resp.status == 200
    assert resp.json()["pong"] is True


def test_blueprint_prefix_override():
    app = make_app()
    bp = Blueprint("v1", prefix="/v1")

    @bp.get("/ping")
    def ping(req):
        return Response(body="ok")

    app.register(bp, prefix="/v2")
    client = TestClient(app)
    assert client.get("/v2/ping").status == 200
    assert client.get("/v1/ping").status == 404

def test_response_json():
    app = make_app()

    @app.get("/data")
    def data(req):
        return Response.json({"a": 1})

    client = TestClient(app)
    resp = client.get("/data")
    assert resp.content_type == "application/json"
    assert resp.json()["a"] == 1


def test_response_redirect():
    app = make_app()

    @app.get("/go")
    def go(req):
        return Response.redirect("/dest")

    client = TestClient(app)
    resp = client.get("/go")
    assert resp.status == 302
    assert resp.headers.get("Location") == "/dest"


def test_query_params():
    app = make_app()

    @app.get("/search")
    def search(req):
        q = req.query_params.get("q", [None])[0]
        return Response.json({"q": q})

    client = TestClient(app)
    resp = client.get("/search", query={"q": "piu"})
    assert resp.json()["q"] == "piu"


def test_cookies():
    app = make_app()

    @app.get("/set")
    def set_cookie(req):
        resp = Response(body="ok")
        resp.set_cookie("flavor", "choc", max_age=3600)
        return resp

    @app.get("/get")
    def get_cookie(req):
        return Response.json({"flavor": req.cookies.get("flavor")})

    client = TestClient(app)
    client.get("/set")
    resp = client.get("/get")
    assert resp.json()["flavor"] == "choc"


def test_delete_cookie():
    app = make_app()

    @app.get("/set")
    def set_c(req):
        r = Response(body="ok")
        r.set_cookie("tok", "abc", max_age=3600)
        return r

    @app.get("/del")
    def del_c(req):
        r = Response(body="ok")
        r.delete_cookie("tok")
        return r

    @app.get("/check")
    def check(req):
        return Response.json({"tok": req.cookies.get("tok")})

    client = TestClient(app)
    client.get("/set")
    client.get("/del")
    resp = client.get("/check")
    assert resp.json()["tok"] is None

def test_session_persists():
    app = make_app()

    @app.get("/write")
    def write(req):
        req.session["val"] = "hello"
        return Response(body="ok")

    @app.get("/read")
    def read(req):
        return Response.json({"val": req.session.get("val")})

    client = TestClient(app)
    client.get("/write")
    resp = client.get("/read")
    assert resp.json()["val"] == "hello"


def test_session_clear():
    app = make_app()

    @app.get("/write")
    def write(req):
        req.session["x"] = 1
        return Response(body="ok")

    @app.get("/clear")
    def clear(req):
        req.session.clear()
        return Response(body="ok")

    @app.get("/read")
    def read(req):
        return Response.json({"x": req.session.get("x")})

    client = TestClient(app)
    client.get("/write")
    client.get("/clear")
    assert client.get("/read").json()["x"] is None

def test_require_auth_blocks():
    app = make_app()

    @app.get("/secret")
    @require_auth(redirect_to="/login")
    def secret(req):
        return Response(body="secret")

    client = TestClient(app)
    resp = client.get("/secret")
    assert resp.status == 302
    assert resp.headers.get("Location") == "/login"


def test_require_auth_passes():
    app = make_app()

    @app.get("/do-login")
    def do_login(req):
        login_user(req, {"id": 1, "role": "user"})
        return Response(body="ok")

    @app.get("/secret")
    @require_auth
    def secret(req):
        return Response(body="secret")

    client = TestClient(app)
    client.get("/do-login")
    assert client.get("/secret").status == 200


def test_require_auth_role_pass():
    app = make_app()

    @app.get("/do-login")
    def do_login(req):
        login_user(req, {"id": 1, "role": "admin"})
        return Response(body="ok")

    @app.get("/admin")
    @require_auth(role="admin")
    def admin(req):
        return Response(body="admin")

    client = TestClient(app)
    client.get("/do-login")
    assert client.get("/admin").status == 200


def test_require_auth_role_fail():
    app = make_app()

    @app.get("/do-login")
    def do_login(req):
        login_user(req, {"id": 1, "role": "user"})
        return Response(body="ok")

    @app.get("/admin")
    @require_auth(role="admin")
    def admin(req):
        return Response(body="admin")

    client = TestClient(app)
    client.get("/do-login")
    assert client.get("/admin").status == 403


def test_logout():
    app = make_app()

    @app.get("/do-login")
    def do_login(req):
        login_user(req, {"id": 1, "role": "user"})
        return Response(body="ok")

    @app.get("/do-logout")
    def do_logout(req):
        logout_user(req)
        return Response(body="ok")

    @app.get("/secret")
    @require_auth(redirect_to="/login")
    def secret(req):
        return Response(body="secret")

    client = TestClient(app)
    client.get("/do-login")
    assert client.get("/secret").status == 200
    client.get("/do-logout")
    assert client.get("/secret").status == 302

def test_rate_limit_per_route():
    app = make_app()

    @app.get("/limited")
    @rate_limit(limit=2, window=60)
    def limited(req):
        return Response(body="ok")

    client = TestClient(app)
    assert client.get("/limited").status == 200
    assert client.get("/limited").status == 200
    assert client.get("/limited").status == 429

def test_plugin_adds_route():
    app = make_app()

    class PingPlugin(Plugin):
        name = "ping"
        def setup(self, app):
            @app.get("/ping")
            def ping(req):
                return Response.json({"ping": True})

    app.register_plugin(PingPlugin())
    client = TestClient(app)
    assert client.get("/ping").json()["ping"] is True

def test_background_tasks_run():
    app = PIU()
    app.middleware.use(SessionMiddleware(secret_key="test"))
    app.middleware.use(CSRFMiddleware(exempt_paths=["/"]))

    results = []

    async def async_task(val):
        results.append(f"async:{val}")

    def sync_task(val):
        results.append(f"sync:{val}")

    @app.get("/go")
    def go(req):
        req.background_tasks.add(async_task, "a")
        req.background_tasks.add(sync_task, "b")
        return Response(body="ok")

    client = TestClient(app)
    client.get("/go")
    assert "async:a" in results
    assert "sync:b" in results

def test_config_dict():
    app = PIU(config={"MY_KEY": "hello"})
    assert app.config["MY_KEY"] == "hello"


def test_config_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nNUM=42\nFLAG=true\n")
    app = PIU()
    app.config.from_env_file(str(env))
    assert app.config["FOO"] == "bar"
    assert app.config["NUM"] == 42
    assert app.config["FLAG"] is True


def test_config_cast():
    app = PIU(config={"PORT": "8080", "DEBUG": "true", "RATIO": "1.5"})
    assert app.config["PORT"] == "8080"
    app.config.from_dict({"PORT": 8080, "DEBUG": True, "RATIO": 1.5})
    assert app.config["PORT"] == 8080
    assert app.config["DEBUG"] is True
    assert app.config["RATIO"] == 1.5

def test_openapi_schema():
    app = make_app()
    app.enable_docs(title="Test API")

    @app.get("/items/<id>")
    def get_item(req, id: str):
        return Response.json({"id": id})

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status == 200
    schema = resp.json()
    assert schema["info"]["title"] == "Test API"
    assert "/items/{id}" in schema["paths"]


def test_swagger_ui():
    app = make_app()
    app.enable_docs()
    client = TestClient(app)
    resp = client.get("/docs")
    assert resp.status == 200
    assert b"swagger" in resp.body.lower()