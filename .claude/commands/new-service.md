---
description: Scaffold a new Verra backend microservice (Python/FastAPI) under code/backend/services.
argument-hint: [service name]
---
Use the `verra-backend-service` skill. Create **$1** with app/main.py (+/health), pyproject.toml,
Dockerfile, tests, README; wire it into code/backend/docker-compose.yml and CI. Public traffic only via
the gateway; talk to other services over HTTP+mTLS; conform to api/openapi.yaml.
