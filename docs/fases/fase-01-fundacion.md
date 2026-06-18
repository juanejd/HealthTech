# Fase 01 — Fundación e Infraestructura

## Descripción

Establece la estructura base del proyecto: organización de carpetas, sistema de configuración, gestión de variables de entorno y el módulo de logging. Esta fase no requiere hardware real y puede ejecutarse en cualquier máquina de desarrollo.

## Objetivo

Tener un proyecto ejecutable con configuración cargable, logging funcional y estructura de módulos lista para recibir la lógica de negocio en fases posteriores.

---

## Módulos y Archivos

| Archivo                          | Responsabilidad                                                  |
|----------------------------------|------------------------------------------------------------------|
| `backend/main.py`                | Punto de entrada FastAPI + arranque de Uvicorn                   |
| `backend/config/schedules.json`  | Configuración inicial de horarios de dispensación                |
| `backend/modules/logger.py`      | Registro de eventos con timestamp UTC                            |
| `backend/requirements.txt`       | Dependencias Python del proyecto                                 |

---

## Requerimientos que Cubre

| ID    | Descripción                                                      |
|-------|------------------------------------------------------------------|
| RF-6  | El sistema debe registrar todos los eventos con marca temporal UTC. |
| RNF-4 | El software debe ejecutarse sobre Python 3.9+.                   |

---

## Criterios de Aceptación

- [ ] La estructura de carpetas coincide con la especificada en la documentación técnica (sección 9).
- [ ] `backend/main.py` arranca con `uvicorn main:app` sin errores.
- [ ] `logger.py` registra eventos en `backend/logs/events.log` con timestamp UTC en formato ISO 8601.
- [ ] `schedules.json` carga correctamente y valida su estructura mínima (array `schedules` con campos `time`, `days`, `message`, `enabled`).
- [ ] El entorno virtual se activa y todas las dependencias de `requirements.txt` se instalan sin conflictos.

---

## Dependencias

Ninguna. Esta es la fase de arranque.

---

## Comandos de Verificación

```bash
# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Arrancar el servidor (debe responder en http://localhost:8000)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Verificar logging (ejecutar evento de prueba y revisar el log)
cat backend/logs/events.log
```

---

## Notas Técnicas

- El timestamp UTC debe formatearse en ISO 8601: `2026-06-16T08:00:00Z`.
- `schedules.json` es recargado dinámicamente por el Scheduler (Fase 03) — no debe requerir reinicio del servicio.
- Nunca commitear el archivo `.env` real; solo `.env.example`.
