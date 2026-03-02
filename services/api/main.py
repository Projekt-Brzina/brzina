
import urllib.parse
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

# OpenAPI docs endpoint (default at /docs, /openapi.json)
# Optionally, add a custom route for OpenAPI schema
@app.get("/openapi", include_in_schema=False)
async def custom_openapi():
    return app.openapi()

DATABASE_URL = os.getenv("DATABASE_URL")
CAR_SERVICE_URL = os.getenv("CAR_SERVICE_URL", "http://car-car:8000")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking-booking:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-auth:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-payment:8000")
WEATHER_SERVICE_URL = os.getenv("CAR_SERVICE_URL", "http://car-car:8000")  # Weather is in car
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
    async with httpx.AsyncClient(follow_redirects=True) as client:
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
        # Debug: print all outgoing headers
        print("[DEBUG] proxy_request outgoing headers:", headers)
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

# Proxy PATCH /api/bookings/{booking_id}/confirm to booking service
@app.api_route("/api/bookings/{booking_id}/confirm", methods=["PATCH"])
async def bookings_confirm(booking_id: int, request: Request):
    return await proxy_request("PATCH", f"{BOOKING_SERVICE_URL}/bookings/{booking_id}/confirm", request, require_jwt=True)

# Proxy PATCH /api/bookings/{booking_id}/deny to booking service
@app.api_route("/api/bookings/{booking_id}/deny", methods=["PATCH"])
async def bookings_deny(booking_id: int, request: Request):
    return await proxy_request("PATCH", f"{BOOKING_SERVICE_URL}/bookings/{booking_id}/deny", request, require_jwt=True)

# Proxy GET /api/bookings/owner to booking service
@app.api_route("/api/bookings/owner", methods=["GET"])
async def bookings_owner(request: Request):
    return await proxy_request("GET", f"{BOOKING_SERVICE_URL}/bookings/owner", request, require_jwt=True)

# Proxy PATCH /api/bookings/{booking_id}/cancel to booking service
@app.api_route("/api/bookings/{booking_id}/cancel", methods=["PATCH"])
async def bookings_cancel(booking_id: int, request: Request):
    return await proxy_request("PATCH", f"{BOOKING_SERVICE_URL}/bookings/{booking_id}/cancel", request, require_jwt=True)

# Proxy POST /api/payments to payment service
@app.api_route("/api/payments", methods=["POST"])
async def payments_create(request: Request):
    return await proxy_request("POST", f"{PAYMENT_SERVICE_URL}/payments", request, require_jwt=True)
# Proxy route for /api/cars/my (must be above /api/cars/{car_id})
@app.api_route("/api/cars/my", methods=["GET"])
async def cars_my(request: Request):
    # Extract JWT from Authorization header
    auth = request.headers.get("authorization")
    user_id = None
    if auth and auth.lower().startswith("bearer "):
        token = auth[7:]
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("id") or payload.get("user_id")
        except Exception:
            pass
    # Forward all query params, but override/add user_id and tenant_id
    query = dict(request.query_params)
    # Try to extract tenant_id from query or JWT if not present
    tenant_id = query.get("tenant_id")
    if not tenant_id and auth and auth.lower().startswith("bearer "):
        token = auth[7:]
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            tenant_id = payload.get("tenant_id")
        except Exception:
            pass
    if user_id:
        query["user_id"] = str(user_id)
    if tenant_id:
        query["tenant_id"] = str(tenant_id)
    query_str = urllib.parse.urlencode(query)
    url = f"{CAR_SERVICE_URL}/cars/my"
    if query_str:
        url += f"?{query_str}"
    return await proxy_request("GET", url, request, require_jwt=True)




# Cars CRUD (require JWT)


# Accept both /cars, /cars/, /api/cars, /api/cars/ for GET and POST
@app.api_route("/cars", methods=["GET", "POST"])
@app.api_route("/cars/", methods=["GET", "POST"])
@app.api_route("/api/cars", methods=["GET", "POST"])
@app.api_route("/api/cars/", methods=["GET", "POST"])
async def cars_root(request: Request):
    if request.method == "GET":
        return await proxy_request("GET", f"{CAR_SERVICE_URL}/cars/", request, require_jwt=True)
    else:
        # Ensure Content-Type is application/json if not set
        if request.headers.get("content-type", "").startswith("application/json"):
            return await proxy_request("POST", f"{CAR_SERVICE_URL}/cars", request, require_jwt=True)
        else:
            # Rebuild request with correct Content-Type
            data = await request.body()
            headers = dict(request.headers)
            headers["content-type"] = "application/json"
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.post(f"{CAR_SERVICE_URL}/cars", content=data, headers=headers)
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers={k: v for k, v in resp.headers.items() if k.lower() != 'content-encoding'}
                )

@app.api_route("/cars/{car_id}", methods=["GET", "PUT", "DELETE", "PATCH"])
async def cars_detail(car_id: int, request: Request):
    return await proxy_request(request.method, f"{CAR_SERVICE_URL}/cars/{car_id}", request, require_jwt=True)
@app.api_route("/api/cars/{car_id}", methods=["GET", "PUT", "DELETE", "PATCH"])
async def cars_detail_api(car_id: int, request: Request):
    return await proxy_request(request.method, f"{CAR_SERVICE_URL}/cars/{car_id}", request, require_jwt=True)



# Users endpoint (proxied to auth service)
@app.api_route("/api/users", methods=["GET"])
@app.api_route("/api/users/", methods=["GET"])
async def users_root(request: Request):
    return await proxy_request("GET", f"{AUTH_SERVICE_URL}/users", request)

# Also support /users and /users/ for ingress rewrite
@app.api_route("/users", methods=["GET"])
@app.api_route("/users/", methods=["GET"])
async def users_root_rewrite(request: Request):
    return await proxy_request("GET", f"{AUTH_SERVICE_URL}/users", request)


# Bookings CRUD (require JWT)
@app.api_route("/bookings", methods=["GET", "POST"])
@app.api_route("/bookings/", methods=["GET", "POST"])
@app.api_route("/api/bookings", methods=["GET", "POST"])
@app.api_route("/api/bookings/", methods=["GET", "POST"])
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
@app.api_route("/api/auth/register", methods=["POST"])
async def auth_register(request: Request):
    return await proxy_request("POST", f"{AUTH_SERVICE_URL}/auth/register", request)

@app.api_route("/auth/login", methods=["POST"])
@app.api_route("/api/auth/login", methods=["POST"])
async def auth_login(request: Request):
    return await proxy_request("POST", f"{AUTH_SERVICE_URL}/auth/login", request)

@app.api_route("/auth/me", methods=["GET"])
@app.api_route("/api/auth/me", methods=["GET"])
async def auth_me(request: Request):
    return await proxy_request("GET", f"{AUTH_SERVICE_URL}/auth/me", request)

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

# Tenants endpoint (proxied to auth service)
@app.api_route("/api/tenants", methods=["GET"])
@app.api_route("/api/tenants/", methods=["GET"])
async def tenants_root(request: Request):
    return await proxy_request("GET", f"{AUTH_SERVICE_URL}/tenants", request)

# Also support /tenants and /tenants/ for ingress rewrite
@app.api_route("/tenants", methods=["GET"])
@app.api_route("/tenants/", methods=["GET"])
async def tenants_root_rewrite(request: Request):
    return await proxy_request("GET", f"{AUTH_SERVICE_URL}/tenants", request)