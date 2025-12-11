# 🔧 Auphere Backend

**FastAPI Backend Service**

Servicio backend principal de Auphere que orquesta la comunicación entre el frontend, el agente de IA y el microservicio de lugares.

---

## 📋 **Tabla de Contenidos**

- [Descripción](#descripción)
- [Tecnologías](#tecnologías)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Docker](#docker)
- [Troubleshooting](#troubleshooting)

---

## 📝 **Descripción**

El backend de Auphere es una API REST construida con FastAPI que proporciona:

- **Autenticación y autorización** con Auth0
- **Gestión de usuarios** y preferencias
- **Orquestación** entre Agent y Places services
- **Caché** con Redis para optimizar rendimiento
- **Integración** con servicios externos (Google Places, Perplexity)

---

## 🛠️ **Tecnologías**

- **Framework:** FastAPI 0.115+
- **Python:** 3.11+
- **Base de datos:** PostgreSQL (via Supabase o directo)
- **Caché:** Redis 7+
- **Autenticación:** Auth0
- **ASGI Server:** Uvicorn

### **Dependencias Principales**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic[email]==2.12.5
httpx==0.27.2
redis==5.2.1
sqlalchemy>=2.0.36
PyJWT>=2.10.1
```

---

## ✅ **Requisitos Previos**

### **Opción 1: Docker**
- Docker >= 24.0
- Docker Compose >= 2.20

### **Opción 2: Local**
- Python 3.11+
- PostgreSQL 17+ (o acceso a Supabase)
- Redis 7+
- pip o poetry

---

## 📦 **Instalación**

### **Opción 1: Con Docker (Recomendado)**

Ver [README principal](../README.md) para instrucciones de Docker Compose.

### **Opción 2: Desarrollo Local**

```bash
# Navegar al directorio del backend
cd auphere-backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ **Configuración**

### **Variables de Entorno**

Crea un archivo `.env` en `auphere-backend/`:

```env
# ============================================
# Auth0 Configuration
# ============================================
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://auphere-api

# ============================================
# External API Keys
# ============================================
GOOGLE_PLACES_API_KEY=your_google_places_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key

# ============================================
# Internal Services
# ============================================
PLACES_SERVICE_URL=http://localhost:8002
PLACES_SERVICE_ADMIN_TOKEN=dev-admin-token
PLACES_SERVICE_DEFAULT_CITY=Zaragoza
PLACES_SERVICE_TIMEOUT=10.0

GPT_BACKEND_URL=http://localhost:8001
GPT_BACKEND_WS_URL=ws://localhost:8001

# ============================================
# Redis Configuration
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL_SECONDS=3600

# ============================================
# FastAPI Configuration
# ============================================
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# ============================================
# CORS Configuration
# ============================================
FRONTEND_URL=http://localhost:3000

# ============================================
# Environment
# ============================================
ENVIRONMENT=development
```

### **Tabla de Variables**

| Variable | Descripción | Requerido | Valor por Defecto |
|----------|-------------|-----------|-------------------|
| `AUTH0_DOMAIN` | Dominio de Auth0 | ✅ | - |
| `AUTH0_AUDIENCE` | API Audience | ✅ | `https://auphere-api` |
| `GOOGLE_PLACES_API_KEY` | API Key de Google Places | ⚠️ | - |
| `PERPLEXITY_API_KEY` | API Key de Perplexity | ⚠️ | - |
| `PLACES_SERVICE_URL` | URL del microservicio Places | ✅ | `http://localhost:8002` |
| `PLACES_SERVICE_ADMIN_TOKEN` | Token de admin | ✅ | - |
| `GPT_BACKEND_URL` | URL del Agent service | ✅ | `http://localhost:8001` |
| `REDIS_HOST` | Host de Redis | ✅ | `localhost` |
| `REDIS_PORT` | Puerto de Redis | ✅ | `6379` |
| `API_HOST` | Host del servidor | ✅ | `0.0.0.0` |
| `API_PORT` | Puerto del servidor | ✅ | `8000` |
| `FRONTEND_URL` | URL del frontend (CORS) | ✅ | `http://localhost:3000` |
| `ENVIRONMENT` | Entorno de ejecución | ✅ | `development` |

---

## 🏃 **Ejecución**

### **Desarrollo Local**

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar con hot reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O usar el entry point
python app/main.py
```

### **Con Docker**

```bash
# Desde la raíz del proyecto
docker-compose up backend

# O build y run
docker build -t auphere-backend .
docker run -p 8000:8000 --env-file .env auphere-backend
```

### **Verificar que funciona**

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## 📚 **API Endpoints**

### **Autenticación**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login de usuario |
| POST | `/api/v1/auth/register` | Registro de usuario |
| POST | `/api/v1/auth/logout` | Logout de usuario |
| GET | `/api/v1/auth/me` | Obtener usuario actual |

### **Places**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/places/search` | Buscar lugares |
| GET | `/api/v1/places/{place_id}` | Obtener detalle de lugar |
| GET | `/api/v1/places/nearby` | Lugares cercanos |

### **Plans**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/plans/create` | Crear plan de viaje |
| GET | `/api/v1/plans/{plan_id}` | Obtener plan |
| GET | `/api/v1/plans/user` | Planes del usuario |

### **Chat**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/chat/message` | Enviar mensaje al agent |
| GET | `/api/v1/chat/history` | Historial de conversación |
| WS | `/api/v1/chat/ws` | WebSocket para chat en tiempo real |

### **Health & Docs**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (solo desarrollo) |
| GET | `/redoc` | ReDoc UI (solo desarrollo) |

---

## 🧪 **Testing**

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Ver reporte
open htmlcov/index.html
```

### **Estructura de Tests**

```
auphere-backend/
├── tests/
│   ├── test_auth.py
│   ├── test_places.py
│   ├── test_plans.py
│   └── test_chat.py
```

---

## 🐳 **Docker**

### **Build**

```bash
docker build -t auphere-backend:latest .
```

### **Run**

```bash
docker run -p 8000:8000 \
  -e AUTH0_DOMAIN=your-tenant.auth0.com \
  -e AUTH0_AUDIENCE=https://auphere-api \
  -e PLACES_SERVICE_URL=http://places:8002 \
  -e GPT_BACKEND_URL=http://agent:8001 \
  -e REDIS_HOST=redis \
  auphere-backend:latest
```

### **Dockerfile**

El Dockerfile usa multi-stage build para optimizar el tamaño:

- **Stage 1 (builder):** Instala dependencias
- **Stage 2 (runtime):** Copia solo lo necesario

---

## 🔧 **Troubleshooting**

### **Error: Auth0 connection failed**

```bash
# Verificar credenciales de Auth0
curl "https://${AUTH0_DOMAIN}/.well-known/openid-configuration"

# Verificar que AUTH0_DOMAIN no incluye https://
echo $AUTH0_DOMAIN  # Debe ser: your-tenant.auth0.com
```

### **Error: Cannot connect to Places service**

```bash
# Verificar que Places está corriendo
curl http://localhost:8002/health

# Verificar PLACES_SERVICE_URL
echo $PLACES_SERVICE_URL
```

### **Error: Redis connection failed**

```bash
# Verificar que Redis está corriendo
redis-cli ping

# Si usa Docker
docker-compose ps redis
```

### **Error: Module not found**

```bash
# Reinstalar dependencias
pip install -r requirements.txt

# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## 📁 **Estructura del Proyecto**

```
auphere-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuración
│   ├── dependencies.py      # Dependencias de FastAPI
│   ├── models/              # Modelos Pydantic
│   │   ├── auth.py
│   │   ├── places.py
│   │   └── plans.py
│   ├── routers/             # Endpoints
│   │   ├── auth.py
│   │   ├── places.py
│   │   ├── plans.py
│   │   └── chat.py
│   ├── services/            # Lógica de negocio
│   │   ├── google_places.py
│   │   ├── gpt_backend_client.py
│   │   └── redis_client.py
│   └── utils/               # Utilidades
│       ├── amenities_mapper.py
│       ├── feature_inference.py
│       └── normalizers.py
├── tests/                   # Tests
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔗 **Enlaces Útiles**

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Auth0 Python SDK](https://auth0.com/docs/quickstart/backend/python)
- [Redis Python Client](https://redis-py.readthedocs.io/)

---

## 📝 **Notas de Desarrollo**

### **Hot Reload**

El servidor se reinicia automáticamente al detectar cambios en el código cuando se ejecuta con `--reload`.

### **Logs**

Los logs se imprimen en stdout. En producción, usar un logging centralizado.

### **CORS**

CORS está configurado para permitir requests desde `FRONTEND_URL`. Modificar en `app/main.py` si es necesario.

---

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request
