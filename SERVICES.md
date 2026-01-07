# SERVICES (auphere-backend)

Este servicio expone un **gateway REST** para el frontend bajo el prefijo ` /api/v1 `.

## Convenciones

- **Formato de error**: FastAPI `HTTPException` (`detail`) o el error propio del microservicio proxied.
- **Streaming**: Server-Sent Events (SSE) cuando se usa el agent.

## Health

### `GET /health`

- **Devuelve**: estado del servicio.

## Places (proxy a `auphere-places`)

Base: ` /api/v1/places `

### `GET /places/search`

Proxy a `GET {PLACES_SERVICE_URL}/places/search`.

- **Query params** (principales):
  - `city` (opcional, default `PLACES_SERVICE_DEFAULT_CITY`)
  - `q` (opcional)
  - `type` (opcional)
  - `lat`, `lon` (opcionales)
  - `radius_km` (opcional)
  - `min_rating` (opcional)
  - `page` (default 1)
  - `limit` (default 20)
- **Devuelve**:
  - `{ places: PlaceResponse[], total, page, per_page, total_pages }`

### `POST /places/search`

Mismo proxy pero aceptando body `PlaceSearchRequest` (contrato interno del backend) y traduciéndolo a query params para `auphere-places`.

### `GET /places/{place_id}`

Proxy a `GET {PLACES_SERVICE_URL}/places/{place_id}`.

- **Notas**:
  - `place_id` puede ser **Google Place ID** o UUID interno (si el cliente lo tiene).
  - Adjunta `photos`, `reviews`, `tips` en `custom_attributes` para consumo del frontend.

### `GET /places/clusters`

Proxy a `GET {PLACES_SERVICE_URL}/places/clusters` (DBSCAN PostGIS).

- **Query params** (según soporte en places):
  - `city`, `type`, `lat`, `lon`, `radius_km`
  - `eps_m`, `min_points`
  - `limit_places`, `limit_clusters`
- **Devuelve**: payload de clusters del microservicio `auphere-places`.

## Chat (proxy a `auphere-agent`)

Base: ` /api/v1/chat `

### `POST /chat`

Envía un mensaje al agent y retorna respuesta “no streaming”.

### `POST /chat/stream`

Streaming SSE de la respuesta del agent.

- **Devuelve**: eventos SSE (`event: ...` + `data: ...`), incluyendo `end` con `{ places, plan }` normalizados.

## Plans

Base: ` /api/v1/plans `

CRUD de planes (router interno del backend; puede integrarse luego con el agent/DB según roadmap).

## Geocoding (proxy Google Maps API)

Base: ` /api/v1/geocoding `

Estos endpoints existen para **ocultar la API key** al frontend.

- Requiere `GOOGLE_PLACES_API_KEY`.


