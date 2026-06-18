# Referencia de API — HealthTech

API REST + WebSocket del backend FastAPI. Todos los endpoints REST se montan bajo el
prefijo `/api`; el WebSocket vive en la raíz.

- **URL base (desarrollo):** `http://localhost:8000`
- **Formato:** JSON en peticiones y respuestas.
- **CORS:** permitido para `http://localhost:3000` y `http://localhost:5173`.
- **Autenticación:** ninguna. El servicio está pensado para una red local de confianza.
- **Documentación interactiva:** FastAPI expone Swagger UI en `/docs` y ReDoc en `/redoc`.

---

## Índice de endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/status` | Estado consolidado del sistema. |
| GET | `/api/schedules` | Obtener horarios configurados. |
| PUT | `/api/schedules` | Reemplazar el conjunto de horarios. |
| GET | `/api/logs` | Historial de eventos de dispensación. |
| POST | `/api/dispense` | Ejecutar un ciclo de dispensación. |
| POST | `/api/diagnostic/step` | Avanzar el servo un compartimento. |
| POST | `/api/diagnostic/home` | Llevar el carrusel a la posición home (0). |
| GET | `/api/diagnostic/weight` | Leer el peso actual de la celda. |
| POST | `/api/diagnostic/tare` | Tarar la balanza (poner a cero). |
| WS | `/ws/status` | Notificaciones de estado en tiempo real. |

---

## Estado

### `GET /api/status`

Devuelve el estado consolidado del sistema.

**Respuesta `200 OK`**

```json
{
  "current_day": "lunes",
  "compartment_index": 1,
  "next_event": "2026-06-18T20:00:00Z",
  "last_event": {
    "timestamp": "2026-06-18T08:00:12Z",
    "type": "dispense",
    "status": "OK",
    "extraction_detected": true,
    "day": "lunes",
    "compartment_index": 1
  },
  "wifi_connected": true,
  "is_busy": false
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `current_day` | string | Nombre del día actual en español (UTC). |
| `compartment_index` | int | Compartimento del día actual (lunes=1 … domingo=7). |
| `next_event` | string \| null | Próximo evento programado (ISO-8601 UTC) o `null` si no hay. |
| `last_event` | object \| null | Último evento registrado, o `null` si no hay historial. |
| `wifi_connected` | bool | Estado de conectividad. |
| `is_busy` | bool | `true` si hay una dispensación en curso. |

---

## Horarios

### `GET /api/schedules`

Devuelve los horarios configurados. Si el archivo no existe o es inválido, devuelve una
lista vacía.

**Respuesta `200 OK`**

```json
{
  "schedules": [
    {
      "time": "08:00",
      "days": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
      "message": "Es hora de tomar su medicamento de la mañana.",
      "enabled": true
    }
  ]
}
```

### `PUT /api/schedules`

Reemplaza **todo** el conjunto de horarios y recarga el planificador en caliente (sin
reiniciar el servicio).

**Cuerpo de la petición**

```json
{
  "schedules": [
    {
      "time": "08:00",
      "days": ["lunes", "miércoles", "viernes"],
      "message": "Es hora de tomar su medicamento.",
      "enabled": true
    }
  ]
}
```

| Campo | Tipo | Reglas |
|---|---|---|
| `time` | string | Formato `HH:MM` 24 h (`00:00`–`23:59`). Validado por regex. |
| `days` | string[] | Nombres de día en español: `lunes`…`domingo`. |
| `message` | string | Mensaje de recordatorio. |
| `enabled` | bool | Si el horario está activo. |

**Respuesta `200 OK`** — devuelve el objeto guardado (mismo formato que el cuerpo).

**Respuesta `422 Unprocessable Entity`** — si `time` no cumple `HH:MM`:

```json
{
  "detail": [
    {
      "loc": ["body", "schedules", 0, "time"],
      "msg": "Value error, Invalid time format: '8:00'. Expected HH:MM (00:00-23:59).",
      "type": "value_error"
    }
  ]
}
```

---

## Registros

### `GET /api/logs`

Devuelve el historial completo de eventos, **del más reciente al más antiguo**.

**Respuesta `200 OK`**

```json
{
  "events": [
    {
      "timestamp": "2026-06-18T08:00:12Z",
      "type": "dispense",
      "status": "OK",
      "extraction_detected": true,
      "day": "lunes",
      "compartment_index": 1
    }
  ],
  "total": 1
}
```

---

## Dispensación

### `POST /api/dispense`

Ejecuta un ciclo de dispensación completo: posiciona el carrusel en el compartimento del
día actual, tara la balanza y espera la confirmación de retiro por caída de peso.

Mientras corre, marca el sistema como ocupado (`is_busy = true`) y rechaza acciones
manuales de diagnóstico (HTTP 409).

**Petición:** sin cuerpo.

**Respuesta `200 OK`**

```json
{
  "status": "OK",
  "extraction_detected": true,
  "timestamp": "2026-06-18T08:00:12Z"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `status` | string | `"OK"` si se detectó el retiro; `"FAIL"` si no, o si el sensor falló. |
| `extraction_detected` | bool | `true` si se confirmó la caída de peso. |
| `timestamp` | string | Marca temporal UTC del evento (ISO-8601). |

> Si el HX711 falla (`HX711Error`), el resultado es `status: "FAIL"` y
> `extraction_detected: false` — nunca se confirma una dispensación con el sensor caído.
> El evento se registra en el log y se encola una notificación para tolerancia a fallos.

---

## Diagnóstico (`/api/diagnostic`)

Control manual de hardware para pruebas y mantenimiento. **Todos** los endpoints de
escritura rechazan la operación con **HTTP 409** si hay una dispensación en curso.

### `POST /api/diagnostic/step`

Avanza el servo un compartimento (un paso).

**Respuesta `200 OK`**

```json
{ "status": "ok", "position": 2 }
```

**Respuesta `409 Conflict`** (dispensación activa)

```json
{ "detail": { "status": "busy", "detail": "dispense_active" } }
```

### `POST /api/diagnostic/home`

Lleva el carrusel a la posición home (índice 0).

**Respuesta `200 OK`**

```json
{ "status": "ok", "position": 0 }
```

### `GET /api/diagnostic/weight`

Lee el peso actual de la celda de carga.

**Respuesta `200 OK`**

```json
{ "status": "ok", "weight_g": 4.2, "calibrated": true }
```

| Campo | Tipo | Descripción |
|---|---|---|
| `weight_g` | float | Peso actual. En gramos si `calibrated` es `true`; cuentas crudas del ADC si no. |
| `calibrated` | bool | `true` si hay un factor de calibración cargado desde archivo. |

**Respuesta `503 Service Unavailable`** (sensor caído)

```json
{ "detail": { "status": "error", "detail": "sensor_unavailable" } }
```

### `POST /api/diagnostic/tare`

Tara la balanza (fija el cero de referencia) y devuelve la lectura resultante.

**Respuesta `200 OK`**

```json
{ "status": "ok", "weight_g": 0.0, "calibrated": true }
```

Mismos errores que `weight`: `409` si ocupado, `503` si el sensor falla.

---

## WebSocket

### `WS /ws/status`

Canal de notificaciones en tiempo real. Tras cada dispensación, el backend hace
**broadcast** del resultado a todos los clientes conectados.

**Mensaje emitido por el servidor**

```json
{
  "status": "OK",
  "extraction_detected": true,
  "timestamp": "2026-06-18T08:00:12Z"
}
```

El frontend usa esta señal como disparador para re-consultar `GET /api/status` y refrescar
la UI. El cliente puede enviar texto (se ignora); la conexión se mantiene abierta hasta que
una de las partes la cierra. El cliente de referencia (`src/services/api.js`) reintenta la
conexión cada 3 s si se cae.

---

## Ejemplos

**cURL**

```bash
# Estado del sistema
curl http://localhost:8000/api/status

# Dispensar
curl -X POST http://localhost:8000/api/dispense

# Actualizar horarios
curl -X PUT http://localhost:8000/api/schedules \
  -H "Content-Type: application/json" \
  -d '{"schedules":[{"time":"08:00","days":["lunes"],"message":"Tomar medicamento","enabled":true}]}'

# Leer peso
curl http://localhost:8000/api/diagnostic/weight
```

**JavaScript (fetch)**

```javascript
const BASE_URL = "http://localhost:8000";

const status = await fetch(`${BASE_URL}/api/status`).then((r) => r.json());

const result = await fetch(`${BASE_URL}/api/dispense`, { method: "POST" }).then((r) =>
  r.json(),
);

// WebSocket
const ws = new WebSocket(BASE_URL.replace(/^http/, "ws") + "/ws/status");
ws.onmessage = (e) => console.log("Evento:", JSON.parse(e.data));
```

---

## Documentos relacionados

- [README](../README.md) — instalación y puesta en marcha.
- [Arquitectura](./arquitectura.md) — diseño del sistema.
- [Guía de usuario](./guia-usuario.md) — uso cotidiano.
