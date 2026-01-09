# auphere-backend

Gateway API (FastAPI) para Auphere.

- Expone endpoints estables para el frontend bajo `/api/v1/*`
- Hace proxy/orquestación hacia:
  - `auphere-agent` (IA + streaming SSE)
  - `auphere-places` (SoT de lugares: search/detail/clusters)
- Gestión de planes (CRUD)
- Autenticación con Auth0

> Este servicio **no** realiza enrichment de lugares. Todo lo "places" vive en `auphere-places`.

## Tecnologías

- **Framework:** FastAPI 0.115+
- **Base de datos:** PostgreSQL (SQLAlchemy async)
- **Caché:** Redis
- **Auth:** Auth0 (JWT)
- **Analytics:** PostHog (Cloud en producción)
- **Python:** 3.9+

## Requisitos

- Python 3.9+
- Redis 7+
- PostgreSQL
- Servicios internos:
  - `auphere-agent` en `http://localhost:8001`
  - `auphere-places` en `http://localhost:8002`

## Instalación (local)

```bash
cd auphere-backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuración

Crea `.env` en `auphere-backend/`:

```env
# Environment
ENVIRONMENT=development

# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://auphere-api

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/auphere

# Internal services
PLACES_SERVICE_URL=http://localhost:8002
GPT_BACKEND_URL=http://localhost:8001

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL_SECONDS=3600

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000

# CORS
FRONTEND_URL=http://localhost:3000

# PostHog (opcional en local - usa console.log)
POSTHOG_ENABLED=false
# POSTHOG_API_KEY=phc_xxx  # Solo producción
# POSTHOG_HOST=https://eu.i.posthog.com
```

### Variables de PostHog (Analytics)

| Variable | Descripción | Requerido | Valor por Defecto |
|----------|-------------|-----------|-------------------|
| `POSTHOG_ENABLED` | Habilitar PostHog | ⚠️ | `false` |
| `POSTHOG_API_KEY` | Project API Key (solo producción) | ⚠️ | - |
| `POSTHOG_HOST` | Host de PostHog | ⚠️ | `https://eu.i.posthog.com` |

> **Nota:** En desarrollo (`ENVIRONMENT=development`), PostHog usa console logging. En producción, envía a PostHog Cloud.

## Ejecutar

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verificación rápida

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| POST | `/api/v1/chat/stream` | Chat con streaming SSE |
| GET | `/api/v1/plans` | Listar planes del usuario |
| POST | `/api/v1/plans` | Crear plan |
| GET | `/api/v1/plans/{id}` | Obtener plan |
| PATCH | `/api/v1/plans/{id}` | Actualizar plan |
| DELETE | `/api/v1/plans/{id}` | Eliminar plan |

## Docker

```bash
docker build -t auphere-backend:latest .
docker run -p 8000:8000 --env-file .env auphere-backend:latest
```
