# Auphere Backend API

Backend API para Auphere construido con FastAPI y Supabase.

## 🚀 Características

- ✅ Autenticación completa (Login, Register, Forgot Password, Reset Password)
- ✅ Integración con Supabase Auth
- ✅ Gestión de perfiles de usuario
- ✅ CORS configurado para desarrollo
- ✅ Validación de datos con Pydantic
- ✅ Documentación automática con Swagger/OpenAPI

## 📋 Requisitos Previos

- Python 3.9 o superior
- Proyecto de Supabase configurado
- Variables de entorno configuradas

## 🔧 Configuración

### 1. Clonar/Crear archivo de entorno

Duplica el archivo `.env.example` y renómbralo a `.env`:

```bash
cp .env.example .env
```

### 2. Configurar variables de entorno

Edita el archivo `.env` con tus credenciales de Supabase:

```env
# Supabase Configuration - New API Key System
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_tu_clave_aqui
SUPABASE_API_KEY=sb_api_key_tu_clave_aqui

# GPT Backend Gateway
GPT_BACKEND_URL=http://localhost:8001
GPT_BACKEND_WS_URL=ws://localhost:8001/ws/chat

# Auphere Places microservice
PLACES_SERVICE_URL=http://127.0.0.1:3001
# Solo si protegiste los endpoints administrativos
PLACES_SERVICE_ADMIN_TOKEN=admin-token-dev-change-me-in-production
PLACES_SERVICE_DEFAULT_CITY=Zaragoza
PLACES_SERVICE_TIMEOUT=10

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Configuration
FRONTEND_URL=http://localhost:3000

# Environment
ENVIRONMENT=development
```

**Obtener credenciales de Supabase (Nuevo Sistema de API Keys):**

1. Ve a tu proyecto en [Supabase Dashboard](https://app.supabase.com)
2. Ve a **Settings > API**
3. Copia las **nuevas claves API** (recomendado):
   - **Project URL** → `SUPABASE_URL`
   - **Publishable Key** (`sb_publishable_...`) → `SUPABASE_PUBLISHABLE_KEY` (para frontend y operaciones normales)
   - **API Key** (`sb_api_key_...`) → `SUPABASE_API_KEY` (⚠️ SOLO backend, mantener secreto)

**Nota sobre claves antiguas:**

- Las claves antiguas (`anon` y `service_role`) aún funcionan pero están siendo deprecadas
- El sistema soporta ambas claves durante la migración
- Se recomienda migrar al nuevo sistema lo antes posible
- Ver `MIGRATION_GUIDE.md` para más detalles sobre la migración

### 3. Conectar el servicio `auphere-places`

El backend ahora consume el microservicio `auphere-places` (Rust) como única fuente de datos de lugares. Antes de levantar FastAPI:

1. Sigue el `QUICKSTART.md` del repo `auphere-places` para correr el servicio y ejecutar las migraciones (`./run_migrations.sh`).
2. Lanza una sincronización manual (`POST /admin/sync/Zaragoza`) para tener datos locales.
3. Actualiza tus variables `PLACES_SERVICE_*` en `.env`. Puedes cambiar `PLACES_SERVICE_DEFAULT_CITY` cuando sumemos más ciudades.

### 4. Configurar base de datos en Supabase

Ejecuta el siguiente SQL en el SQL Editor de Supabase:

```sql
-- Crear tabla de perfiles
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  name text not null,
  email text not null,
  avatar_url text,
  preferences jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Habilitar Row Level Security
alter table public.profiles enable row level security;

-- Políticas de seguridad
-- Los usuarios pueden leer su propio perfil
create policy "Users can view own profile"
  on profiles for select
  using (auth.uid() = id);

-- Los usuarios pueden actualizar su propio perfil
create policy "Users can update own profile"
  on profiles for update
  using (auth.uid() = id);

-- Permitir inserción desde el trigger (security definer)
create policy "Enable insert for authenticated users only"
  on profiles for insert
  with check (true);

-- Función para crear perfil automáticamente
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, name, email, avatar_url, preferences)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', 'User'),
    new.email,
    null,
    '{}'::jsonb
  );
  return new;
end;
$$;

-- Eliminar trigger existente si existe
drop trigger if exists on_auth_user_created on auth.users;

-- Trigger para crear perfil cuando se registra un usuario
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Función para actualizar updated_at automáticamente
create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$;

-- Eliminar trigger existente si existe
drop trigger if exists on_profile_updated on public.profiles;

-- Trigger para actualizar updated_at
create trigger on_profile_updated
  before update on public.profiles
  for each row execute procedure public.handle_updated_at();
```

### 5. Configurar URLs de redirección en Supabase

1. Ve a Authentication > URL Configuration
2. Agrega en **Site URL**: `http://localhost:3000`
3. Agrega en **Redirect URLs**:
   - `http://localhost:3000/**`
   - `http://localhost:5173/**`
   - Tu dominio de producción (cuando esté listo)

### 6. (Opcional) Deshabilitar confirmación de email en desarrollo

Para facilitar las pruebas en desarrollo:

1. Ve a Authentication > Settings
2. Desactiva **"Enable email confirmations"**

⚠️ **Importante:** Re-activar en producción.

## 🏃 Ejecutar el Servidor

### Opción 1: Con uvicorn directamente

```bash
# Desde la carpeta auphere-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Opción 2: Con Python directamente

```bash
# Desde la carpeta auphere-backend
python -m app.main
```

### Opción 3: Con el script run.sh (crear si prefieres)

```bash
#!/bin/bash
cd "$(dirname "$0")"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📦 Instalación de Dependencias

Si es la primera vez que ejecutas el proyecto:

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🌐 Endpoints Disponibles

### Autenticación

- `POST /api/v1/auth/register` - Registrar nuevo usuario
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/forgot-password` - Solicitar reset de contraseña
- `POST /api/v1/auth/reset-password` - Resetear contraseña con token
- `GET /api/v1/auth/me` - Obtener información del usuario actual (requiere autenticación)
- `POST /api/v1/auth/logout` - Cerrar sesión (requiere autenticación)

### Otros

- `GET /` - Mensaje de bienvenida
- `GET /health` - Health check
- `GET /docs` - Documentación interactiva Swagger (solo en desarrollo)

## 📝 Ejemplos de Uso

### Registrar usuario

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "password": "password123"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "password123"
  }'
```

### Obtener información del usuario (requiere token)

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🧪 Testing

El servidor incluye documentación interactiva disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔒 Seguridad

- ✅ Row Level Security (RLS) habilitado en Supabase
- ✅ Validación de tokens JWT
- ✅ CORS configurado para desarrollo
- ✅ Nuevo sistema de API Keys de Supabase
- ⚠️ **Importante:** Nunca expongas `SUPABASE_API_KEY` en el frontend o repositorios públicos

### Nuevas API Keys de Supabase

El proyecto usa el nuevo sistema de claves API de Supabase:

- **Publishable Key** (`sb_publishable_...`):

  - ✅ Segura para usar en frontend
  - ✅ Respeta políticas RLS
  - ✅ Reemplaza a `anon key`

- **API Key** (`sb_api_key_...`):
  - ❌ NUNCA exponer en frontend
  - ✅ Solo para operaciones backend administrativas
  - ✅ Bypassa políticas RLS
  - ✅ Reemplaza a `secret/service_role key` legacy

Ver `MIGRATION_GUIDE.md` para más información sobre el cambio de sistema de autenticación.

## 📁 Estructura del Proyecto

```
auphere-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración y settings
│   ├── dependencies.py      # Dependencias (Supabase, auth)
│   ├── models/              # Modelos Pydantic
│   │   ├── __init__.py
│   │   └── auth.py
│   └── routers/             # Routers de la API
│       ├── __init__.py
│       └── auth.py
├── .env.example            # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt        # Dependencias Python
└── README.md              # Este archivo
```

## 🐛 Solución de Problemas

### Error: "Missing Supabase environment variables"

- Verifica que el archivo `.env` existe y tiene todas las variables necesarias
- Asegúrate de que los nombres de las variables sean correctos (sin espacios, etc.)

### Error: "Invalid authentication credentials"

- Verifica que las credenciales de Supabase sean correctas
- Asegúrate de que el token JWT sea válido y no haya expirado

### Error: "User profile not found"

- Verifica que el trigger `on_auth_user_created` esté funcionando
- Verifica que la tabla `profiles` tenga la política RLS correcta

### CORS Error

- Verifica que `FRONTEND_URL` en `.env` coincida con la URL del frontend
- Verifica que las URLs estén en `allow_origins` en `main.py`

## 📚 Recursos

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)

## 👥 Contribuir

1. Crea una rama para tu feature
2. Realiza tus cambios
3. Crea un Pull Request

## 📄 Licencia

MIT
