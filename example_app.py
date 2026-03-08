from piu import (
    PIU, Blueprint, Request, Response,
    SessionMiddleware, CSRFMiddleware,
    RateLimitMiddleware, rate_limit,
    require_auth, login_user, logout_user, current_user,
)

app = PIU(template_dir="templates", static_dir="static", static_url="/static")


app.middleware.use(RateLimitMiddleware(limit=100, window=60))   
app.middleware.use(SessionMiddleware(secret_key="super-secret-change-me", max_age=3600))
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

@app.get("/settings")
@require_auth(redirect_to="/login")
async def settings(request: Request):
    return Response(body="<h1>Settings</h1>")



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



if __name__ == "__main__":
    app.run(port=5000)
