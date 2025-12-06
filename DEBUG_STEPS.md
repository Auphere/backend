# 🔍 Pasos para Debuggear la Configuración

## Paso 1: Verificar la Configuración

Ejecuta el script de verificación:

```bash
cd /Users/lmatos/Workspace/auphere/auphere-backend
source venv/bin/activate
python verify_config.py
```

Este script te mostrará:
- ✅ Qué variables están configuradas
- ✅ Qué sistema de claves está usando (nuevo vs legacy)
- ✅ Si las claves son válidas
- ❌ Errores específicos si algo falla

## Paso 2: Problemas Comunes

### ❌ Error: "Invalid API key"

**Causa:** La clave no tiene el formato correcto o no es válida.

**Solución:**

1. Ve a tu Dashboard de Supabase: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a: **Settings** > **API**
4. Busca la sección **"Project API keys"**

**IMPORTANTE:** Copia las claves EXACTAMENTE como aparecen, sin:
- ❌ Espacios al inicio o final
- ❌ Comillas (" o ')
- ❌ Saltos de línea

### ❌ Error: Variables NOT_SET

Si el script muestra `NOT_SET`:

1. Verifica que el archivo `.env` esté en: `/Users/lmatos/Workspace/auphere/auphere-backend/.env`
2. Verifica que las variables NO tengan espacios alrededor del `=`:

**❌ Incorrecto:**
```bash
SUPABASE_URL = https://xxx.supabase.co
SUPABASE_ANON_KEY = "eyJhbGc..."
```

**✅ Correcto:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Paso 3: Formato del Archivo .env

Tu archivo `.env` debe verse así:

### Opción A: Sistema Nuevo (Recomendado)

```bash
# Supabase Configuration
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxxxxxxxxxxx
SUPABASE_API_KEY=sb_api_key_xxxxxxxxxxxxx

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Configuration
FRONTEND_URL=http://localhost:5173

# Environment
ENVIRONMENT=development
```

### Opción B: Sistema Legacy (JWT)

```bash
# Supabase Configuration
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Configuration
FRONTEND_URL=http://localhost:5173

# Environment
ENVIRONMENT=development
```

## Paso 4: Reiniciar el Servidor

Después de corregir el `.env`:

```bash
# Terminal donde corre el backend
# Presiona Ctrl+C para detener
# Luego reinicia:
cd /Users/lmatos/Workspace/auphere/auphere-backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Paso 5: Verificar con el Endpoint de Debug

Con el servidor corriendo, en otra terminal:

```bash
curl http://localhost:8000/debug/config | python -m json.tool
```

Deberías ver algo como:

```json
{
  "status": "ok",
  "supabase_url": "https://tuproyecto.supabase.co",
  "keys_configured": {
    "client_api_key": "eyJhbGci...último8chars",
    "admin_api_key": "eyJhbGci...último8chars"
  },
  "key_types": {
    "using_new_keys": false,
    "using_legacy_keys": true
  }
}
```

## 🆘 Si Nada Funciona

Copia y pega la salida de estos comandos:

```bash
cd /Users/lmatos/Workspace/auphere/auphere-backend
python verify_config.py
```

Y compártela conmigo para ayudarte mejor.

