# Brzina Codebase Guide for AI Agents

## Architecture Overview

**Brzina** is a multi-tenant car sharing microservices platform. The system decomposes into independent FastAPI services that share a single PostgreSQL database with tenant isolation via the `tenant_id` field.

### Service Boundaries

- **auth**: User registration, login, JWT token generation
- **car**: Car inventory management and status
- **booking**: Booking requests/confirmations with temporal validation
- **payment**: Payment processing with mock payment gateway reference
- **api**: Gateway/orchestration service (minimal in current state)
- **template**: Example service template for new features

Each service has the pattern:
```
service/
├── Dockerfile           # Python 3.12 slim, uvicorn on port 8000
├── requirements.txt     # FastAPI, uvicorn, asyncpg
└── app/
    ├── main.py         # FastAPI app factory with startup/shutdown hooks
    ├── config.py       # Settings from environment (DATABASE_URL, JWT secrets)
    ├── db.py           # Global asyncpg connection pool management
    ├── models.py       # Pydantic request/response schemas
    ├── [security.py]   # Auth-specific: password hashing, JWT creation
    └── routers/        # FastAPI routers with business logic
```

### Data Flow

All services share a schema defined in [../infra/db/init.sql](../infra/db/init.sql):
1. **Tenants** table ensures multi-tenant isolation
2. Each entity (users, cars, bookings, payments) includes `tenant_id` foreign key
3. Services enforce tenant scoping in queries (e.g., `WHERE tenant_id=$2`)

Example tenant-scoped query pattern from [../services/auth/app/routers/auth.py](../services/auth/app/routers/auth.py):
```python
await conn.fetchrow(
    "SELECT id FROM users WHERE email=$1 AND tenant_id=$2",
    user.email, user.tenant_id
)
```

## Deployment & Infrastructure

### Docker Build
Each service builds independently: `docker build -t brzina-{service}:latest services/{service}`

### Kubernetes (K8s) Orchestration
- **Namespace**: `brzina` (single namespace for all services)
- **Database**: StatefulSet postgres at `postgres.brzina.svc.cluster.local:5432`
- **Ingress**: NGINX ingress routes `/api/*` to `api` service, `/` to frontend
- **Deployment pattern**: One deployment per service with `imagePullPolicy: IfNotPresent`

See [../infra/k8s/](../infra/k8s/) for manifests. Services connect via K8s DNS (e.g., `auth.brzina.svc.cluster.local`).

## Critical Patterns & Conventions

### Connection Pooling
All services use a **global asyncpg connection pool** initialized at startup:
```python
# services/*/app/db.py pattern
_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(str(settings.database_url))
    return _pool
```
FastAPI startup/shutdown events ensure pool lifecycle management. **Always await `get_pool()` in routes**, never store pool references as class attributes.

### Settings & Environment
All services use Pydantic `BaseSettings` loading from environment:
- `DATABASE_URL`: PostgreSQL connection string (default: K8s cluster DNS)
- `JWT_SECRET`: Signing key for tokens (default: "supersecret" in local dev)
- `JWT_ALGORITHM`: Always "HS256"

See [../services/auth/app/config.py](../services/auth/app/config.py) for the pattern. Services also support `.env` files in local development.

### Authentication & Tenancy
- Auth service generates JWTs with payload: `{"sub": user_id, "tenant_id": tenant_id, "exp": expiration}`
- Tokens expire in 60 minutes (configurable via `jwt_expiration_minutes`)
- Other services must validate tokens and extract `tenant_id` for data scoping
- Passwords hashed with bcrypt; never store plaintext

### Router Organization
FastAPI routers live in `routers/` subdirectories and are included in `main.py`:
```python
app.include_router(auth.router)  # Each router has prefix="/endpoint" and tags
```
Health check endpoints (`routers/health.py`) are standard across services.

## Developer Workflows

### Local Development
1. Ensure PostgreSQL is running and accessible
2. Set `DATABASE_URL` environment variable
3. Install dependencies: `pip install -r services/{service}/requirements.txt`
4. Run service: `uvicorn services/{service}/app/main:app --reload`
5. API docs: `http://localhost:8000/docs` (auto-generated Swagger UI)

### K8s Deployment (Using KIND)
- Build images: `docker build -t brzina-{service}:latest services/{service}`
- Load into KIND cluster: `kind load docker-image brzina-{service}:latest`
- Apply manifests: `kubectl apply -f infra/k8s/`
- Access via ingress: `http://brzina.local/api/...` (requires `/etc/hosts` entry)

### Database Changes
- Add migrations to [../infra/db/init.sql](../infra/db/init.sql)
- All tables must include `tenant_id` and `created_at` timestamp
- Foreign key constraints cascade on tenant deletion

## Service-Specific Notes

- **Auth**: Handles user lifecycle; other services should call via REST or verify JWT locally
- **Booking**: Must validate `start_time < end_time` and check car availability
- **Payment**: Mock payment gateway stores reference in `mock_ref` field; no real gateway integrated
- **Car**: Status field supports 'active', 'inactive', 'maintenance' (extensible enum)
- **API Service**: Largely a gateway; consider it the entry point for cross-service orchestration

## Common Pitfalls

1. **Forgetting tenant_id in queries** — Data leaks between tenants if queries don't filter by tenant
2. **Not awaiting async operations** — All DB calls must use `await`; connection pool acquisition must be awaited
3. **Hardcoding credentials** — Always use environment variables and `settings` object
4. **Ignoring port 8000 binding** — All services bind to `0.0.0.0:8000`; verify no conflicts in K8s deployments
