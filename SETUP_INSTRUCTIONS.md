# 🚀 Instrucciones para Levantar el Backend

## Pasos Rápidos

### 1. Configurar variables de entorno

```bash
cd /Users/lmatos/Workspace/auphere/auphere-backend
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales reales de Supabase:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_tu_clave
SUPABASE_API_KEY=sb_api_key_tu_clave
GPT_BACKEND_URL=http://localhost:8001
GPT_BACKEND_WS_URL=ws://localhost:8001/ws/chat
FRONTEND_URL=http://localhost:3000
```

**Importante:** Usa las **nuevas API Keys** de Supabase (Settings > API):
- `sb_publishable_...` (reemplaza anon key)
- `sb_api_key_...` (reemplaza secret/service_role key)

### 2. Crear y activar entorno virtual (recomendado)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Supabase (una sola vez)

1. Ve a tu proyecto en [Supabase Dashboard](https://app.supabase.com)
2. Ejecuta el SQL del README.md en el SQL Editor
3. Configura las URLs de redirección en Authentication > URL Configuration

### 5. Levantar el servidor

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en: **http://localhost:8000**

## ✅ Verificar que funciona

1. Visita: http://localhost:8000
2. Deberías ver: `{"message": "Welcome to Auphere API", ...}`
3. Visita: http://localhost:8000/docs
4. Deberías ver la documentación interactiva Swagger

## 🔍 Endpoints disponibles

- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/forgot-password` - Solicitar reset
- `POST /api/v1/auth/reset-password` - Resetear contraseña
- `GET /api/v1/auth/me` - Info del usuario (requiere token)
- `POST /api/v1/auth/logout` - Logout (requiere token)

## 📝 Notas

- El servidor se recarga automáticamente si haces cambios (gracias a `--reload`)
- La documentación Swagger está en `/docs`
- Los logs aparecerán en la consola

