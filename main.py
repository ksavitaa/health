import json
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

EMAIL = "22f3002678@ds.study.iitm.ac.in"   # <-- put your logged-in email here

app = FastAPI()

# CORS so the grader's web page can call us from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()
request_count = 0                 # the turnstile counter
LOGS = deque(maxlen=1000)         # the diary (keeps the latest 1000 entries)


@app.middleware("http")
async def observe(request: Request, call_next):
    global request_count
    request_count += 1                       # click the counter for EVERY request
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    entry = {
        "level": "INFO",
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "request_id": request_id,
        "method": request.method,
        "status": response.status_code,
    }
    LOGS.append(entry)
    print(json.dumps(entry), flush=True)     # also show it in the server logs
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/work")
def work(n: int = 1):
    total = 0
    for i in range(min(max(n, 0), 1_000_000)):   # "do K units of work"
        total += i
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    text = (
        "# HELP http_requests_total Total HTTP requests received.\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {request_count}\n"
    )
    return PlainTextResponse(text, media_type="text/plain; version=0.0.4")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": float(time.time() - START_TIME)}


@app.get("/logs/tail")
def logs_tail(limit: int = Query(default=10, ge=0)):
    if limit == 0:
        return []
    return list(LOGS)[-limit:]