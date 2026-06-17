# Fase 05 — Backend API (FastAPI)

## Descripción

Implementa la capa de API REST y WebSocket que expone el sistema al dashboard React. FastAPI corre en la propia Raspberry Pi servido por Uvicorn en el puerto 8000 y se comunica directamente con los módulos Python de las fases anteriores.

## Objetivo

El dashboard puede consultar el estado del sistema, modificar horarios, revisar el historial de eventos y ejecutar dispensaciones manuales a través de una API REST bien definida. El estado en tiempo real se propaga vía WebSocket.

---

## Módulos y Archivos

| Archivo                            | Responsabilidad                                              |
|------------------------------------|--------------------------------------------------------------|
| `backend/main.py`                  | Configuración FastAPI + montaje de routers + arranque CORS  |
| `backend/api/routes_schedules.py`  | GET y PUT `/api/schedules`                                   |
| `backend/api/routes_status.py`     | GET `/api/status`                                            |
| `backend/api/routes_logs.py`       | GET `/api/logs`                                              |
| `backend/api/routes_dispense.py`   | POST `/api/dispense`                                         |
| `backend/api/websocket.py`         | WebSocket `/ws/status`                                       |

---

## Endpoints

| Método | Ruta             | Descripción                                                          |
|--------|------------------|----------------------------------------------------------------------|
| GET    | `/api/schedules` | Retorna la lista actual de horarios configurados                     |
| PUT    | `/api/schedules` | Actualiza horarios y notifica al Scheduler para recarga en caliente  |
| GET    | `/api/status`    | Estado actual: día activo, próximo evento, conectividad              |
| GET    | `/api/logs`      | Historial de eventos con timestamps UTC                              |
| POST   | `/api/dispense`  | Dispara dispensación manual inmediata                                |
| WS     | `/ws/status`     | Actualizaciones de estado en tiempo real                             |

---

## Contratos de Datos

### GET /api/status — Response

```json
{
  "current_day": "lunes",
  "compartment_index": 0,
  "next_event": "2026-06-17T08:00:00Z",
  "last_event": {
    "timestamp": "2026-06-16T08:00:00Z",
    "status": "OK",
    "extraction_detected": true
  },
  "telegram_connected": true,
  "wifi_connected": true
}
```

### PUT /api/schedules — Request Body

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

### GET /api/logs — Response

```json
{
  "events": [
    {
      "timestamp": "2026-06-16T08:00:00Z",
      "type": "dispense",
      "status": "OK",
      "extraction_detected": true,
      "day": "lunes",
      "compartment_index": 0
    }
  ],
  "total": 1
}
```

---

## Requerimientos que Cubre

| ID    | Descripción                                                              |
|-------|--------------------------------------------------------------------------|
| RF-5  | Modificación dinámica de horarios sin reiniciar el servicio.             |
| RF-6  | Historial de eventos con marca temporal UTC accesible desde el dashboard. |

---

## Criterios de Aceptación

- [ ] Todos los endpoints responden con código 200 en el happy path.
- [ ] `PUT /api/schedules` persiste el cambio en `config/schedules.json` y el Scheduler lo recarga sin reiniciar.
- [ ] `POST /api/dispense` ejecuta la misma secuencia que la dispensación automática y retorna el resultado (OK/FAIL).
- [ ] `GET /api/logs` retorna todos los eventos del archivo `logs/events.log` en orden cronológico descendente.
- [ ] El WebSocket `/ws/status` emite un mensaje de estado cada vez que ocurre un evento de dispensación.
- [ ] CORS está configurado para aceptar peticiones del frontend React (dominio `localhost:3000` en desarrollo).
- [ ] La API valida los tipos de datos de entrada con Pydantic y retorna 422 con detalle del error si la validación falla.
- [ ] `GET /api/status` retorna el estado de conectividad Wi-Fi y Telegram en tiempo real.

---

## Dependencias

- **Fase 01** — estructura base y logging.
- **Fase 02** — `servo_controller`, `sensor_manager`.
- **Fase 03** — `scheduler`, `tts_engine`, `fault_tolerance`.
- **Fase 04** — `telegram_bot`.

---

## Instalación

```bash
pip install fastapi uvicorn
```

## Ejecución

```bash
# Desde backend/
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Notas Técnicas

- Usar Pydantic V2 para los modelos de request/response.
- El WebSocket debe usar `ConnectionManager` para manejar múltiples clientes simultáneos de forma segura.
- `POST /api/dispense` debe ejecutarse en un `BackgroundTask` para no bloquear la respuesta HTTP mientras el servo se mueve.
- Configurar CORS con `CORSMiddleware` de FastAPI aceptando `http://localhost:3000` y `http://<ip-raspberry>:3000` en desarrollo.
- Los logs se parsean desde el archivo `events.log` en tiempo de request; no se necesita base de datos para el MVP.
