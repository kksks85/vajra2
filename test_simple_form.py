from fastapi import FastAPI, Form
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="test-secret-key")

@app.get("/test-login")
def test_login_get():
    return {"message": "GET /test-login works"}

@app.post("/test-login")
def test_login_post(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "password": password}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
