
# Brzina
Car sharing platform — multi-tenant, microservices-based, with a Vue frontend and Kubernetes deployment.

## Architecture
- **Microservices:** auth, car, booking, payment, api (gateway), template
- **Database:** PostgreSQL (multi-tenant)
- **Messaging:** Kafka (for booking/payment events)
- **Frontend:** Vue 3 (Vite, Dockerized)
- **Orchestration:** Kubernetes (Helm charts for all services)
- **API Gateway:** FastAPI-based, JWT validation, aggregation, proxying

## Developer Setup
1. Clone repo, install Docker & Python 3.12
2. Start Postgres (see Helm or infra/db/init.sql for schema)
3. For each service:
	- `pip install -r requirements.txt`
	- `uvicorn app.main:app --reload`
4. Frontend:
	- `cd frontend && npm install && npm run dev`
5. Access API docs at `/docs` for each service

## API Documentation
- Each service exposes OpenAPI docs at `/docs`
- API gateway aggregates/proxies all endpoints at `/api/*`
- Example: `POST /api/auth/login`, `GET /api/cars`, `GET /api/bookings/{id}/details`


## Deployment
- Build Docker images for each service and frontend
- Use Helm charts in `helm/` to deploy to Kubernetes
- Example: `helm install auth ./helm/auth`
- CI/CD pipeline: see `.github/workflows/ci-cd.yaml`

### Azure AKS Deployment
1. Create an AKS cluster and connect with `az aks get-credentials`
2. Create namespaces:
	- `kubectl apply -f infra/k8s/namespace.yaml`
	- `kubectl apply -f infra/k8s/ingress-controller.yaml` (for NGINX ingress)
3. Deploy Postgres, Kafka, and all services using Helm:
	- `helm install postgres ./helm/postgres`
	- `helm install kafka ./helm/kafka`
	- `helm install auth ./helm/auth` (repeat for car, booking, payment, api, frontend)
4. Deploy ingress:
	- `helm install ingress ./helm/ingress`
5. Add a DNS record for your AKS ingress IP to point to `brzina.local` or use the public IP directly
6. Access the app at `http://brzina.local` or the assigned IP

## Features
- Multi-tenancy (tenant_id in all tables and JWTs)
- Kafka-based messaging (booking/payment)
- Event sourcing & CQRS (booking)
- GraphQL endpoint (car service)
- External API integration (OpenWeatherMap in car)
- Centralized logging (structlog, JSON)
- Prometheus metrics (`/metrics` on each service)

## Contributing
See `.github/copilot-instructions.md` for AI agent and developer conventions.
