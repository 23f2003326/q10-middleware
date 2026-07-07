import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

EMAIL = "23f2003326@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-lgqxoh.example.com",
    "https://exam.sanand.workers.dev",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIMIT = 10
WINDOW = 10
clients = defaultdict(list)


@app.middleware("http")
async def middleware(request: Request, call_next):
    # -------- Request ID (set BEFORE call_next!) --------
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id   # ✅ now available inside route handler

    # -------- Rate Limit --------
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= LIMIT:
        resp = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        resp.headers["X-Request-ID"] = request_id
        return resp

    clients[client].append(now)

    # -------- Continue --------
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/ping")
async def ping(request: Request):
    return JSONResponse({
        "email": EMAIL,
        "request_id": request.state.request_id   # ✅ always set now
    })


@app.get("/debug")
def debug():
    return {"email_constant": EMAIL}