# Configuración de Variables de Entorno

## ⚠️ Error Actual: Invalid API key

Este error ocurre cuando las claves de Supabase no están correctamente configuradas en tu archivo `.env`.

## Cómo Obtener las Claves Correctas de Supabase

### Opción 1: Sistema Nuevo de API Keys (Recomendado) ✅

1. Ve a tu proyecto en Supabase Dashboard
2. Navega a: **Settings** > **API**
3. Busca la sección **"Project API keys"**
4. Copia estas dos claves:
   - **Publishable key** (comienza con `sb_publishable_...`)
   - **API key** (comienza con `sb_api_key_...`)

### Opción 2: Sistema Legacy (JWT)

Si tu proyecto usa el sistema antiguo:

1. Ve a: **Settings** > **API**
2. Busca la sección **"Project API keys"**
3. Copia estas claves:
   - **anon / public** (JWT largo que comienza con `eyJhbGc...`)
   - **service_role** (JWT largo que comienza con `eyJhbGc...`)

## Configuración del Archivo `.env`

Crea o edita el archivo `/Users/lmatos/Workspace/auphere/auphere-backend/.env`:

### Si usas el Sistema Nuevo:

```bash
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
SUPABASE_API_KEY=sb_api_key_xxx

# GPT Backend
GPT_BACKEND_URL=http://localhost:8001
GPT_BACKEND_WS_URL=ws://localhost:8001/ws/chat

# Auphere Places microservice
PLACES_SERVICE_URL=http://127.0.0.1:3001
PLACES_SERVICE_ADMIN_TOKEN=admin-token-dev-change-me-in-production
PLACES_SERVICE_DEFAULT_CITY=Zaragoza
PLACES_SERVICE_TIMEOUT=10

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Configuration
FRONTEND_URL=http://localhost:5173

# Environment
ENVIRONMENT=development
```

### Si usas el Sistema Legacy:

```bash
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Si usas legacy, deja estas vacías o no las incluyas:
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_API_KEY=

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Auphere Places microservice (igual que en el sistema nuevo)
PLACES_SERVICE_URL=http://127.0.0.1:3001
PLACES_SERVICE_ADMIN_TOKEN=admin-token-dev-change-me-in-production
PLACES_SERVICE_DEFAULT_CITY=Zaragoza
PLACES_SERVICE_TIMEOUT=10

# CORS Configuration
FRONTEND_URL=http://localhost:5173

# Environment
ENVIRONMENT=development
```

## ⚠️ Importante

1. **NUNCA** compartas estas claves públicamente
2. **NUNCA** las incluyas en commits de Git
3. El archivo `.env` ya está en `.gitignore` para protegerte
4. La `API_KEY` (o las claves legacy `SERVICE_ROLE_KEY`) tienen acceso completo a tu base de datos

## Verificación

Después de configurar el `.env`:

1. Detén el servidor de FastAPI (Ctrl+C)
2. Reinicia el servidor:
   ```bash
   cd /Users/lmatos/Workspace/auphere/auphere-backend
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Intenta el registro nuevamente

## Debugging

Si sigues teniendo problemas, verifica:

```python
# Puedes agregar esto temporalmente en app/main.py para debug:
from app.config import settings

@app.get("/debug/config")
def debug_config():
    return {
        "supabase_url": settings.supabase_url,
        "has_publishable_key": bool(settings.supabase_publishable_key),
        "has_api_key": bool(settings.supabase_api_key),
        "has_anon_key": bool(settings.supabase_anon_key),
        "has_service_role": bool(settings.supabase_service_role_key),
        "client_key_length": len(settings.client_api_key) if settings.client_api_key else 0,
        "admin_key_length": len(settings.admin_api_key) if settings.admin_api_key else 0,
    }
```

Luego visita: `http://localhost:8000/debug/config` (¡Elimina esto después de debuggear!)
