import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "23f2003326@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-lgqxoh.example.com",
    "https://exam.sanand.workers.dev",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

LIMIT = 10
WINDOW = 10

clients = defaultdict(list)


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # ---------- Skip rate limit for preflight ----------
    if request.method == "OPTIONS":
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ---------- Rate limiting ----------
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    clients[client] = [
        t for t in clients[client]
        if now - t < WINDOW
    ]

    if len(clients[client]) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    clients[client].append(now)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.get("/debug")
async def debug():
    return {
        "email": EMAIL,
        "limit": LIMIT,
        "window": WINDOW,
        "allowed_origins": ALLOWED_ORIGINS,
    }