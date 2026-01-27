
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
import structlog
import logging
from prometheus_fastapi_instrumentator import Instrumentator

import os
import asyncpg
import httpx
import jwt
from fastapi import HTTPException


def setup_logging():
    logging.basicConfig(format="%(message)s", stream=None, level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

setup_logging()
logger = structlog.get_logger("api-gateway")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

DATABASE_URL = os.getenv("DATABASE_URL")
CAR_SERVICE_URL = os.getenv("CAR_SERVICE_URL", "http://car:8000")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment:8000")
WEATHER_SERVICE_URL = os.getenv("CAR_SERVICE_URL", "http://car:8000")  # Weather is in car
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def get_jwt_payload(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None

async def proxy_request(method, url, request: Request, with_body=True, require_jwt=False):
    async with httpx.AsyncClient() as client:
        params = dict(request.query_params)
        headers = dict(request.headers)
        data = await request.body() if with_body else None
        # JWT validation and context forwarding
        user_ctx = get_jwt_payload(request)
        if require_jwt and not user_ctx:
            raise HTTPException(status_code=401, detail="Missing or invalid JWT")
        if user_ctx:
            headers["x-user-id"] = str(user_ctx.get("sub", ""))
            headers["x-tenant-id"] = str(user_ctx.get("tenant_id", ""))
        try:
            resp = await client.request(
                method,
                url,
                params=params,
                content=data if with_body else None,
                headers={k: v for k, v in headers.items() if k.lower() != 'host'},
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={k: v for k, v in resp.headers.items() if k.lower() != 'content-encoding'}
            )
        except httpx.RequestError as e:
            return Response(content=str(e), status_code=status.HTTP_502_BAD_GATEWAY)

@app.get("/health")
async def health():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.close()
        logger.info("health_check", status="ok")
        return {"status": "ok"}
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {"status": "error", "details": str(e)}


# Cars CRUD (require JWT)
@app.api_route("/cars", methods=["GET", "POST"])
async def cars_root(request: Request):
    return await proxy_request(request.method, f"{CAR_SERVICE_URL}/cars", request, require_jwt=True)

@app.api_route("/cars/{car_id}", methods=["GET", "PUT", "DELETE"])
async def cars_detail(car_id: int, request: Request):
    return await proxy_request(request.method, f"{CAR_SERVICE_URL}/cars/{car_id}", request, require_jwt=True)

# Bookings CRUD (require JWT)
@app.api_route("/bookings", methods=["GET", "POST"])
async def bookings_root(request: Request):
    return await proxy_request(request.method, f"{BOOKING_SERVICE_URL}/bookings", request, require_jwt=True)

@app.api_route("/bookings/{booking_id}", methods=["GET", "PUT", "DELETE"])
async def bookings_detail(booking_id: int, request: Request):
    return await proxy_request(request.method, f"{BOOKING_SERVICE_URL}/bookings/{booking_id}", request, require_jwt=True)

# Aggregation endpoint: booking details (booking + car + payment)
@app.get("/bookings/{booking_id}/details")
async def booking_details(booking_id: int, request: Request):
    user_ctx = get_jwt_payload(request)
    if not user_ctx:
        raise HTTPException(status_code=401, detail="Missing or invalid JWT")
    tenant_id = user_ctx.get("tenant_id")
    headers = {"authorization": request.headers.get("authorization", "")}
    async with httpx.AsyncClient() as client:
        # Get booking
        booking_resp = await client.get(f"{BOOKING_SERVICE_URL}/bookings/{booking_id}", headers=headers)
        if booking_resp.status_code != 200:
            return Response(content=booking_resp.content, status_code=booking_resp.status_code)
        booking = booking_resp.json()
        # Get car
        car_resp = await client.get(f"{CAR_SERVICE_URL}/cars/{booking['car_id']}?tenant_id={tenant_id}", headers=headers)
        car = car_resp.json() if car_resp.status_code == 200 else None
        # Get payment
        payment_resp = await client.get(f"{PAYMENT_SERVICE_URL}/payments?tenant_id={tenant_id}", headers=headers)
        payments = payment_resp.json() if payment_resp.status_code == 200 else []
        payment = next((p for p in payments if p["booking_id"] == booking_id), None)
        return {"booking": booking, "car": car, "payment": payment}

# Auth endpoints
@app.api_route("/auth/register", methods=["POST"])
async def auth_register(request: Request):
    return await proxy_request("POST", f"{AUTH_SERVICE_URL}/auth/register", request)

@app.api_route("/auth/login", methods=["POST"])
async def auth_login(request: Request):
    return await proxy_request("POST", f"{AUTH_SERVICE_URL}/auth/login", request)

# Payments endpoints
@app.api_route("/payments", methods=["GET", "POST"])
async def payments_root(request: Request):
    return await proxy_request(request.method, f"{PAYMENT_SERVICE_URL}/payments", request)

@app.api_route("/payments/{payment_id}", methods=["GET", "PUT", "DELETE"])
async def payments_detail(payment_id: int, request: Request):
    return await proxy_request(request.method, f"{PAYMENT_SERVICE_URL}/payments/{payment_id}", request)

# Weather endpoint (proxied to car service)
@app.get("/weather/{city}")
async def weather(city: str, request: Request):
    return await proxy_request("GET", f"{WEATHER_SERVICE_URL}/weather/{city}", request, with_body=False)