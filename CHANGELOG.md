# Changelog - Auphere Backend

## [2024-11-29] - Migración a Nuevas API Keys de Supabase

### 🔄 Cambios Importantes

#### Sistema de Autenticación Actualizado

- **Migrado** de sistema antiguo JWT (`anon_key`, `service_role_key`) al nuevo sistema de API Keys
- **Agregadas** nuevas variables de entorno:
  - `SUPABASE_PUBLISHABLE_KEY` (reemplaza `SUPABASE_ANON_KEY`)
  - `SUPABASE_API_KEY` (reemplaza `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_SECRET_KEY`)
- **Mantenido** soporte para claves antiguas durante la transición (backward compatibility)

### 📝 Archivos Modificados

1. **app/config.py**
   - Agregadas propiedades `client_api_key` y `admin_api_key`
   - Soporte para claves nuevas y antiguas con fallback automático
   - Variables opcionales para migración gradual

2. **app/dependencies.py**
   - Actualizado `get_supabase_client()` para usar `client_api_key`
   - Actualizado `get_supabase_admin_client()` para usar `admin_api_key`
   - Agregado header `apikey` en opciones del cliente
   - Mejorada documentación de cada función

3. **requirements.txt**
   - Actualizado `supabase` de 2.8.0 a 2.10.0

4. **.env.example**
   - Actualizadas variables con nuevos nombres
   - Agregados comentarios sobre claves legacy
   - Actualizado `FRONTEND_URL` a puerto 3000

### 📚 Documentación Nueva

1. **MIGRATION_GUIDE.md** (nuevo)
   - Guía completa de migración paso a paso
   - Explicación de diferencias entre sistemas
   - Troubleshooting común
   - Checklist de migración

2. **README.md** (actualizado)
   - Sección de seguridad ampliada
   - Instrucciones actualizadas para obtener claves
   - Referencias a la guía de migración

3. **SETUP_INSTRUCTIONS.md** (actualizado)
   - Instrucciones con nuevas variables de entorno
   - Notas sobre nuevas API Keys

### ✨ Características

- ✅ Retrocompatibilidad con claves antiguas
- ✅ Migración sin tiempo de inactividad
- ✅ Mejor seguridad con claves identificables por prefijo
- ✅ Documentación completa del proceso de migración
- ✅ Fallback automático a claves antiguas si no están las nuevas

### ⚠️ Notas de Migración

Para migrar a las nuevas claves:

1. Obtén tus nuevas claves de Supabase Dashboard > Settings > API
2. Actualiza tu archivo `.env` con las nuevas variables
3. Reinicia el servidor
4. Una vez verificado que todo funciona, desactiva las claves antiguas
5. Ver `MIGRATION_GUIDE.md` para detalles completos

### 🔗 Referencias

- [Supabase API Keys Documentation](https://supabase.com/docs/guides/api/api-keys)
- [Migration Guide](./MIGRATION_GUIDE.md)

