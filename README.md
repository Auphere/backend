# auphere-backend

Gateway API (FastAPI) para Auphere.

- Expone endpoints estables para el frontend bajo ` /api/v1/* `
- Hace proxy/orquestación hacia:
  - `auphere-agent` (IA + streaming SSE)
  - `auphere-places` (SoT de lugares: search/detail/clusters)

> Este servicio **no** realiza enrichment de lugares. Todo lo “places” vive en `auphere-places`.

## Requisitos

- Python 3.11+
- Redis 7+
- PostgreSQL (según tu configuración)
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
# Auth0 (si usas auth)
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://auphere-api

# Google Places (solo para /geocoding/* proxy; opcional si no usas ese endpoint)
GOOGLE_PLACES_API_KEY=your_google_places_api_key

# Internal services
PLACES_SERVICE_URL=http://localhost:8002
PLACES_SERVICE_DEFAULT_CITY=Zaragoza
PLACES_SERVICE_TIMEOUT=10.0

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
API_RELOAD=true

# CORS
FRONTEND_URL=http://localhost:3000

ENVIRONMENT=development
```

## Ejecutar

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verificación rápida

- `GET /health`
- `GET /docs`

## Contrato de endpoints

Ver `SERVICES.md`.


