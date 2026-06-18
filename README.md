# HealthTech — Dispensador Inteligente de Medicamentos

Dispensador semanal de medicamentos sobre **Raspberry Pi Zero 2W**. Un carrusel rotativo
con un compartimento por día de la semana se posiciona frente al punto de retiro, y una
celda de carga verifica físicamente el retiro del medicamento detectando la caída de peso.

El sistema es una **aplicación full-stack**:

- **Backend** — API REST + WebSocket en **FastAPI** (Python), que controla el hardware vía GPIO.
- **Frontend** — SPA en **React + Vite + Tailwind v4** para el cuidador/administrador.

## Integrantes

- **Stefanía García López**
- **Juan Esteban Jiménez Daza**

---

## Características

- Carrusel semanal de 7 compartimentos (uno por día) accionado por servomotor **SG90**.
- Verificación física del retiro mediante **celda de carga + HX711** (detección por caída de peso).
- Dispensación **automática** según los horarios (planificador APScheduler en proceso).
- Configuración de horarios **en caliente**, sin reiniciar el servicio.
- Registro de eventos con marca temporal UTC.
- Tolerancia a fallos de red: cola persistente de notificaciones pendientes.
- Panel de **diagnóstico** para operar el motor y la balanza manualmente.
- Actualización en tiempo real vía **WebSocket**.
- **Modo mock**: el backend y los tests corren sin hardware en una PC de desarrollo.

---

## Stack tecnológico

| Capa         | Tecnología                                                                 |
| ------------ | -------------------------------------------------------------------------- |
| Backend      | Python 3.9+ (probado en 3.11), FastAPI, Uvicorn, Pydantic v2               |
| Hardware     | `gpiozero` (servo) + `lgpio` (HX711, bit-bang directo)                     |
| Frontend     | React 18, Vite, Tailwind CSS v4                                            |
| Tests        | `pytest` + `pytest-asyncio` (backend), Vitest + Testing Library (frontend) |
| Persistencia | Archivos JSON / JSONL (sin base de datos)                                  |

---

## Estructura del proyecto

```
HealthTech/
├── backend/
│   ├── main.py                 # App FastAPI: monta routers y CORS
│   ├── api/                    # Routers REST + WebSocket
│   │   ├── routes_status.py
│   │   ├── routes_schedules.py
│   │   ├── routes_logs.py
│   │   ├── routes_dispense.py
│   │   ├── routes_diagnostic.py
│   │   └── websocket.py
│   ├── modules/                # Dominio + drivers de hardware
│   │   ├── servo_controller.py # Servo SG90 (carrusel)
│   │   ├── sensor_manager.py   # HX711 (celda de carga)
│   │   ├── scheduler.py        # Horarios y próximo evento
│   │   ├── auto_dispenser.py   # Disparo automático por horario (APScheduler)
│   │   ├── logger.py           # Registro de eventos (JSONL)
│   │   └── fault_tolerance.py  # Cola de notificaciones pendientes
│   ├── config/schedules.json   # Horarios configurados
│   ├── logs/                   # Eventos, posición, calibración, cola
│   ├── scripts/                # Calibración y autotest de hardware
│   └── tests/                  # Suite pytest
├── frontend/
│   └── src/
│       ├── App.jsx             # Layout + pestañas
│       ├── components/         # StatusView, ScheduleView, LogsView, etc.
│       └── services/api.js     # Cliente HTTP + WebSocket
└── docs/                       # Documentación (este directorio)
```

---

## Requisitos previos

- Python 3.9 o superior.
- Node.js 18+ y npm (para el frontend).
- En la Raspberry Pi: `python3-lgpio` (`sudo apt install -y python3-lgpio`).

> En una PC de desarrollo **no** necesitás hardware ni las librerías de GPIO: el backend
> detecta su ausencia y corre en **modo mock**.

---

## Instalación y ejecución

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Servidor de desarrollo (recarga en caliente)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API queda en `http://localhost:8000`. La documentación interactiva (Swagger UI) en
`http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La interfaz queda en `http://localhost:5173`.

### Variables de entorno

| Variable                   | Lado     | Por defecto             | Descripción                                                             |
| -------------------------- | -------- | ----------------------- | ----------------------------------------------------------------------- |
| `VITE_API_URL`             | Frontend | `http://localhost:8000` | URL base del backend.                                                   |
| `HEALTHTECH_MOCK_DISPENSE` | Backend  | `1`                     | En modo mock, si la dispensación simulada se confirma (`1`) o no (`0`). |

---

## Hardware y pines (BCM)

| Elemento          | Pin    | Función                   |
| ----------------- | ------ | ------------------------- |
| Servo SG90        | GPIO18 | PWM del carrusel          |
| HX711 DT (data)   | GPIO17 | Lectura del ADC           |
| HX711 SCK (clock) | GPIO23 | Reloj del protocolo HX711 |

Alimentar el HX711 a **3,3 V**. Mantener todas las tierras (GND) en común.

> **Nota.** El documento de diseño (`healtech_doc.pdf`) sugiere el HX711 en GPIO5/GPIO6; el
> código real usa **GPIO17/GPIO23**. Esta referencia sigue al código.

---

## Calibración de la celda de carga

Sin calibrar, las lecturas de peso son cuentas crudas del ADC, no gramos, y la detección de
retiro no es fiable. En la Raspberry Pi, con la celda montada:

```bash
cd backend
source .venv/bin/activate
python3 scripts/hx711_calibrate.py
```

El script tara la balanza, te pide un peso de referencia conocido, calcula el factor de
calibración y lo persiste en `logs/hx711_calibration.json`. El backend lo carga al arrancar.

---

## Tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

La suite del backend corre completa en modo mock, sin hardware.

---

## Documentación

- **[Arquitectura](./docs/arquitectura.md)** — diseño del sistema, hardware, módulos y flujos.
- **[Referencia de API](./docs/referencia-api.md)** — todos los endpoints REST y el WebSocket.
- **[Guía de usuario](./docs/guia-usuario.md)** — uso cotidiano para el cuidador.

---
