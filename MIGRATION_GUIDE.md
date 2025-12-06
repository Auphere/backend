# 🔄 Guía de Migración: Nuevas API Keys de Supabase

## Contexto

Supabase ha introducido un nuevo sistema de claves API que reemplaza el antiguo sistema JWT basado en `anon key` y `service_role key`.

### Diferencias Clave

| Aspecto | Sistema Antiguo | Sistema Nuevo |
|---------|-----------------|---------------|
| **Clave Pública** | `anon key` (JWT) | `sb_publishable_...` |
| **Clave Privada** | `service_role key` (JWT) | `sb_api_key_...` |
| **Header HTTP** | `Authorization: Bearer` | `apikey` |
| **Formato** | JWT token | API Key string |

### Ventajas del Nuevo Sistema

✅ **Más seguro**: Las claves tienen prefijos identificables  
✅ **Mejor gestión**: Fácil de rotar y desactivar  
✅ **Compatibilidad**: Se puede usar junto con las claves antiguas durante la transición  
✅ **Sin JWT**: Menos overhead de procesamiento

## 🚀 Pasos de Migración

### 1. Obtener las Nuevas Claves

1. Ve a tu proyecto en [Supabase Dashboard](https://app.supabase.com)
2. Navega a **Settings > API**
3. Encontrarás:
   - **Publishable Key** (`sb_publishable_...`) - Para el frontend y operaciones normales
   - **API Key** (`sb_api_key_...`) - Para el backend con acceso completo

### 2. Actualizar Variables de Entorno

Edita tu archivo `.env`:

```env
# Nuevo sistema (recomendado)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_tu_clave_aqui
SUPABASE_API_KEY=sb_api_key_tu_clave_aqui

# Opcional: Mantén las antiguas durante la transición
# SUPABASE_ANON_KEY=tu_anon_key_antigua
# SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key_antigua
```

### 3. Reiniciar el Servidor

```bash
# Detén el servidor actual (Ctrl+C)
# Luego reinicia:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verificar Funcionamiento

1. **Test básico**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test de autenticación**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User",
       "email": "test@example.com",
       "password": "password123"
     }'
   ```

### 5. Actualizar Frontend (si aplica)

Si estás usando el cliente de Supabase en el frontend:

```typescript
// Antes
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

// Después (recomendado)
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_PUBLISHABLE_KEY
)
```

### 6. Desactivar Claves Antiguas

Una vez que todo funcione correctamente:

1. Ve a **Supabase Dashboard > Settings > API**
2. Haz clic en el botón de desactivar junto a las claves antiguas
3. Confirma la desactivación

⚠️ **Importante**: Solo desactiva las claves antiguas después de verificar que todo funciona con las nuevas.

## 🔧 Compatibilidad Durante la Transición

El backend está configurado para soportar **ambos sistemas simultáneamente**:

- Si defines `SUPABASE_PUBLISHABLE_KEY`, se usará esa
- Si no, usará `SUPABASE_ANON_KEY` como fallback
- Para la clave privada se prioriza `SUPABASE_API_KEY`, con fallback a `SUPABASE_SECRET_KEY` y `SUPABASE_SERVICE_ROLE_KEY`

Esto te permite migrar gradualmente sin tiempo de inactividad.

## 🔒 Consideraciones de Seguridad

### ⚠️ NUNCA expongas estas claves

- **`sb_api_key_...`** - NUNCA en el frontend o cliente
- **`sb_api_key_...`** - NUNCA en repositorios públicos
- **`sb_api_key_...`** - Solo en variables de entorno del servidor

### ✅ Usa correctamente

- **`sb_publishable_...`** - Seguro para usar en frontend
- **`sb_publishable_...`** - Respeta las políticas RLS
- **`sb_api_key_...`** - Solo en backend para operaciones administrativas

## 📚 Recursos Adicionales

- [Supabase API Keys Documentation](https://supabase.com/docs/guides/api/api-keys)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

## ❓ Preguntas Frecuentes

### ¿Puedo seguir usando las claves antiguas?

Sí, por ahora. Pero se recomienda migrar al nuevo sistema lo antes posible ya que eventualmente las claves antiguas serán deprecadas.

### ¿Qué pasa si algo falla durante la migración?

El sistema está configurado con fallback a las claves antiguas. Si algo falla, simplemente mantén ambas configuradas hasta resolver el problema.

### ¿Debo actualizar mi base de datos?

No, no se requieren cambios en la base de datos. Solo cambias las claves de autenticación.

### ¿Las Edge Functions funcionan con las nuevas claves?

Las Edge Functions actualmente solo verifican JWT con las claves antiguas. Si usas Edge Functions, deberás usar `--no-verify-jwt` y manejar la autorización manualmente, o mantener las claves antiguas hasta que Supabase actualice el soporte completo.

## 🐛 Troubleshooting

### Error: "Missing Supabase environment variables"

**Solución**: Verifica que `.env` tenga las variables correctamente definidas:
```bash
cat .env | grep SUPABASE
```

### Error: "Invalid API key"

**Solución**: 
1. Verifica que copiaste las claves completas sin espacios
2. Verifica que las claves empiecen con `sb_publishable_` o `sb_api_key_`
3. Reinicia el servidor después de cambiar las variables

### Error de autenticación en requests

**Solución**: Las nuevas claves usan el header `apikey` en lugar de `Authorization: Bearer`. El cliente de Supabase Python maneja esto automáticamente.

## 📝 Checklist de Migración

- [ ] Obtener nuevas claves de Supabase Dashboard
- [ ] Actualizar `.env` con las nuevas claves
- [ ] Mantener claves antiguas como backup
- [ ] Reiniciar servidor backend
- [ ] Probar endpoints de autenticación
- [ ] Actualizar frontend (si aplica)
- [ ] Verificar que todo funciona correctamente
- [ ] Desactivar claves antiguas en Supabase Dashboard
- [ ] Remover claves antiguas del `.env`
- [ ] Documentar la migración en tu equipo

---

**Última actualización**: Noviembre 2024

