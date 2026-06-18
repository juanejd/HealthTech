# HealthTech — Documentación Técnica General

**Proyecto:** Dispensador Inteligente de Medicamentos  
**Versión:** 2.0.0  
**Fecha:** Junio de 2026  
**Autores:** Stefanía García López · Juan Esteban Jiménez Daza  
**Universidad:** Universidad Nacional de Colombia  
**Clasificación:** Uso Académico

---

## 1. Visión Global del Proyecto

### 1.1 Problema

La adherencia terapéutica constituye uno de los principales retos dentro de los sistemas modernos de salud. Pacientes adultos mayores, personas con deterioro cognitivo leve y pacientes polimedicados presentan dificultades recurrentes para recordar horarios de medicación, identificar dosis correctas y mantener continuidad en sus tratamientos farmacológicos. La omisión de medicamentos, la administración incorrecta de dosis y el olvido de horarios son factores críticos que afectan directamente la evolución clínica del paciente.

### 1.2 Solución Propuesta

HealthTech es un dispensador inteligente de medicamentos de funcionamiento semanal, construido sobre una plataforma embebida Linux (Raspberry Pi Zero 2W). El sistema automatiza la dispensación mediante un carrusel rotativo de siete compartimentos (uno por día) y verifica la extracción del medicamento con un sensor de peso, registrando cada evento localmente.

La solución se complementa con un backend FastAPI y un dashboard React.js que permiten al cuidador configurar horarios, visualizar el estado del sistema y consultar el historial de eventos desde cualquier dispositivo en la red local.

### 1.3 Objetivo General

Diseñar e implementar un dispensador inteligente semanal de medicamentos basado en Raspberry Pi Zero 2W, capaz de automatizar la entrega de dosis programadas mediante un sistema de carrusel rotativo, detectar la extracción del medicamento y registrar cada evento localmente.

### 1.4 Objetivos Específicos

1. Diseñar un sistema mecánico rotativo compuesto por siete compartimentos correspondientes a cada día de la semana.
2. Implementar un sistema de control embebido basado en Raspberry Pi Zero 2W utilizando Linux y Python.
3. Implementar sensores de confirmación de retiro del medicamento.
4. Registrar eventos de dispensación en archivos locales con marcas temporales.
5. Diseñar un sistema configurable de horarios de administración sin reinicio del servicio.

---

## 2. Stack Tecnológico

### 2.1 Hardware

| Componente          | Modelo / Especificación       | Función                                                        |
|---------------------|-------------------------------|----------------------------------------------------------------|
| Unidad principal    | Raspberry Pi Zero 2W          | Control central: lógica de dispensación, FastAPI                |
| Servomotor          | SG90                          | Movimiento angular del carrusel semanal de siete compartimentos |
| Sensor de extracción| IR reflectivo o capacitivo     | Detección de retiro del medicamento                             |
| Almacenamiento      | MicroSD 16 GB o superior      | Sistema operativo y persistencia de registros                   |
| Conectividad        | Wi-Fi integrado (RPi Zero 2W) | Red local (dashboard)                                           |
| Alimentación        | Fuente 5V regulada (2A mín.)  | Suministro energético del sistema                               |
| Pulsador            | Push button GPIO               | Confirmación manual o mantenimiento                             |

### 2.2 Software

| Capa        | Tecnología              | Versión mínima | Propósito                                  |
|-------------|-------------------------|----------------|--------------------------------------------|
| SO          | Raspberry Pi OS (Lite)  | Bookworm       | Sistema operativo base                     |
| Runtime     | Python                  | 3.9+           | Lógica embebida y backend                  |
| Backend     | FastAPI                 | 0.100+         | API REST para el dashboard                 |
| Frontend    | React.js                | 18+            | Dashboard de administración                |
| GPIO        | RPi.GPIO o gpiozero     | —              | Control de pines (servo, sensor, pulsador) |
| Servidor ASGI| Uvicorn                | 0.20+          | Servidor para FastAPI                      |

### 2.3 Justificación del Servomotor SG90

El mecanismo de dispensación utiliza un servomotor SG90 por su bajo peso, bajo consumo de corriente y compatibilidad directa con la señal PWM generada desde la Raspberry Pi. Al tratarse de un carrusel semanal liviano (estructura ligera + medicamentos de bajo peso), el torque del SG90 (~1.8 kg·cm a 4.8V) es suficiente para posicionar cada compartimento sin pérdida de precisión angular.

El control se realiza mediante modulación por ancho de pulso (PWM) a 50 Hz:

- Pulso de ~0.5 ms → posición 0°
- Pulso de ~1.5 ms → posición 90°
- Pulso de ~2.5 ms → posición 180°

El desplazamiento angular entre compartimentos está dado por:

```
θ = 360° / 7 ≈ 51.43°
```

Cada compartimento semanal se encuentra separado 51.43° respecto al siguiente en el carrusel.

---

## 3. Arquitectura del Sistema

### 3.1 Descripción General

El sistema adopta una arquitectura centralizada monolítica. La Raspberry Pi Zero 2W ejecuta simultáneamente todas las responsabilidades del sistema: control embebido de hardware, lógica de dispensación, servidor API y conectividad remota. No se utiliza ningún microcontrolador auxiliar externo.

El cuidador accede al dashboard React.js desde cualquier navegador en la red local. El frontend se comunica con la API FastAPI que corre en la propia Raspberry Pi, y esta API interactúa directamente con los módulos de control de hardware a través de GPIO.

### 3.2 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RED LOCAL (Wi-Fi)                            │
│                                                                     │
│  ┌──────────────────┐          HTTP/REST          ┌───────────────┐ │
│  │  PC / Navegador  │ ◄──────────────────────────►│ Raspberry Pi  │ │
│  │                  │    http://<rpi-ip>:8000      │  Zero 2W      │ │
│  │  ┌────────────┐  │                              │               │ │
│  │  │ React.js   │  │                              │  ┌─────────┐  │ │
│  │  │ Dashboard  │  │                              │  │ FastAPI │  │ │
│  │  └────────────┘  │                              │  │ (ASGI)  │  │ │
│  └──────────────────┘                              │  └────┬────┘  │ │
│                                                     │       │       │ │
│                                                     │       ▼       │ │
│                                                     │  ┌─────────┐  │ │
│                                                     │  │ Módulos │  │ │
│                                                     │  │ Python  │  │ │
│                                                     │  └────┬────┘  │ │
│                                                     │       │       │ │
│                                                     │       ▼       │ │
│                                                     │     GPIO      │ │
│                                                     └───────┬───────┘ │
└─────────────────────────────────────────────────────────────┼───────┘
                                                              │
                           ┌──────────────────────────────────┼──────────┐
                           │          HARDWARE FÍSICO         │          │
                           │                                  ▼          │
                           │  ┌──────────┐  ┌────────┐                 │
                           │  │ SG90     │  │Sensor  │                 │
                           │  │ Servo    │  │IR/Cap. │                 │
                           │  │ (PWM)    │  │        │                 │
                           │  └──────────┘  └────────┘                 │
                           │                                            │
                           │  ┌──────────┐                              │
                           │  │Pulsador  │                              │
                           │  │(GPIO)    │                              │
                           │  └──────────┘                              │
                           └────────────────────────────────────────────┘
```

### 3.3 Diagrama de Bloques de Software

```
┌──────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI ZERO 2W                          │
│                    Raspberry Pi OS (Linux)                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI (Uvicorn)                        │  │
│  │                                                            │  │
│  │   /api/schedules    → Gestión de horarios                  │  │
│  │   /api/status       → Estado actual del sistema            │  │
│  │   /api/logs         → Historial de eventos                 │  │
│  │   /api/dispense     → Dispensación manual                  │  │
│  │   /ws/status        → WebSocket de estado en tiempo real   │  │
│  │                                                            │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                              │                                    │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   MÓDULOS PYTHON                           │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │
│  │  │  Scheduler   │  │  Controlador │  │  Gestor          │ │  │
│  │  │  (Horarios)  │  │  Servo SG90  │  │  Sensores        │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Sistema de Logs (eventos con marca temporal UTC)    │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Gestor de Tolerancia a Fallos                       │  │  │
│  │  │  (Cola de eventos pendientes si no hay red)          │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ▼                                    │
│                         GPIO (Pines)                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Interfaces Eléctricas

### 4.1 Asignación de Pines GPIO

| GPIO   | Elemento      | Función                          |
|--------|---------------|----------------------------------|
| GPIO18 | SG90          | Señal PWM del servomotor         |
| GPIO17 | Sensor IR     | Detección de extracción          |
| GPIO27 | Pulsador      | Confirmación manual              |

### 4.2 Consideraciones Eléctricas

- Todas las referencias de tierra (GND) deben permanecer conectadas en común entre la Raspberry Pi, el SG90 y el sensor.
- El SG90 puede alimentarse desde el pin de 5V de la Raspberry Pi en condiciones de carga ligera. Si el carrusel presenta mayor peso mecánico, se recomienda una fuente externa dedicada de 5V para el servo.
- La fuente de alimentación principal debe ser de 5V regulada con capacidad mínima de 2A para cubrir el consumo combinado de la RPi (~350 mA típico), el SG90 (~500–700 mA pico) y los periféricos.

### 4.3 Diagrama de Conexión de Hardware

```
                    FUENTE 5V / 2A
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
     ┌─────────────────┐    ┌──────────────┐
     │ Raspberry Pi    │    │   SG90        │
     │ Zero 2W         │    │   Servomotor  │
     │                 │    │              │
     │  5V ──────────────────► VCC (rojo)  │
     │  GND ─────────────────► GND (marrón)│
     │  GPIO18 ──────────────► Signal (nar)│
     │                 │    └──────────────┘
     │                 │
     │  GPIO17 ◄──── Sensor IR (señal)
     │  3.3V   ────► Sensor IR (VCC)
     │  GND    ────► Sensor IR (GND)
     │                 │
     │  GPIO27 ◄──── Pulsador
     │  GND    ────► Pulsador (con pull-down)
     └─────────────────┘
```

---

## 5. Arquitectura de Software — Módulos

### 5.1 Scheduler (Planificador de Horarios)

Módulo encargado de monitorear continuamente el reloj del sistema y activar eventos de dispensación cuando se alcanza la hora programada. Debe permitir la modificación dinámica de horarios sin reiniciar el servicio (RF-5). Los horarios se almacenan en un archivo de configuración local (JSON o YAML) que el módulo recarga periódicamente o por señal.

### 5.2 Controlador del Servo SG90

Genera la señal PWM en GPIO18 para posicionar el carrusel semanal en el compartimento correspondiente al día actual. El desplazamiento entre compartimentos es de 51.43°. El tiempo entre activación del evento y movimiento del servo no debe superar 200 ms (RNF-2).

### 5.3 Gestor de Sensores

Procesa las señales provenientes del sensor IR reflectivo o capacitivo conectado en GPIO17. Detecta si el medicamento fue retirado del compartimento después de la dispensación. También gestiona la entrada del pulsador físico en GPIO27 para confirmación manual.

### 5.4 Sistema de Logs

Registra todos los eventos de dispensación con marca temporal UTC (RF-6). Los eventos incluyen: activación programada, movimiento del servo y detección/no detección de extracción. Los registros se persisten en archivos locales en la MicroSD.

### 5.5 Gestor de Tolerancia a Fallos

Almacena los eventos pendientes cuando existe pérdida temporal de conexión a Internet (RF-7, RNF-6). Los eventos se sincronizan automáticamente cuando se restablece la conectividad. El sistema debe reiniciar automáticamente servicios críticos ante fallos (RNF-7).

---

## 6. API Backend (FastAPI)

### 6.1 Descripción

FastAPI corre en la propia Raspberry Pi, servido por Uvicorn. Expone endpoints REST que permiten al dashboard React.js gestionar la configuración del sistema, consultar el estado y revisar el historial de eventos. Adicionalmente, un endpoint WebSocket permite al frontend recibir actualizaciones de estado en tiempo real.

### 6.2 Endpoints Principales

| Método | Ruta                | Descripción                                              |
|--------|---------------------|----------------------------------------------------------|
| GET    | `/api/schedules`    | Obtiene la lista de horarios de dispensación configurados |
| PUT    | `/api/schedules`    | Actualiza los horarios sin reiniciar el servicio         |
| GET    | `/api/status`       | Retorna el estado actual del sistema (día, próximo evento, conectividad) |
| GET    | `/api/logs`         | Retorna el historial de eventos con marcas temporales UTC |
| POST   | `/api/dispense`     | Ejecuta una dispensación manual (gira el servo al compartimento actual) |
| WS     | `/ws/status`        | WebSocket para actualizaciones de estado en tiempo real   |

### 6.3 Estructura de Respuesta de Estado (ejemplo)

```json
{
  "current_day": "martes",
  "compartment_index": 2,
  "next_event": "2026-06-17T08:00:00Z",
  "last_event": {
    "timestamp": "2026-06-16T08:00:00Z",
    "status": "OK",
    "extraction_detected": true
  },
  "wifi_connected": true
}
```

### 6.4 Estructura de Horario (ejemplo)

```json
{
  "schedules": [
    {
      "time": "08:00",
      "days": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
      "message": "Es hora de tomar su medicamento de la mañana.",
      "enabled": true
    },
    {
      "time": "20:00",
      "days": ["lunes", "miércoles", "viernes"],
      "message": "Es hora de tomar su medicamento de la noche.",
      "enabled": true
    }
  ]
}
```

---

## 7. Dashboard React.js (Frontend)

### 7.1 Descripción

Dashboard elemental que permite al cuidador interactuar con el sistema desde cualquier navegador en la red local. Se accede a través de `http://<ip-raspberry>:8000`. Durante el desarrollo, el frontend corre en el servidor de desarrollo de React (`npm start`) en la máquina del desarrollador y se conecta a la API FastAPI de la Raspberry Pi.

### 7.2 Vistas del Dashboard

El dashboard se compone de las siguientes vistas mínimas:

**Vista de Estado:** Muestra el estado actual del sistema — día activo, próximo evento programado, estado de conectividad Wi-Fi y resultado del último evento de dispensación (OK / FAIL). Esta vista se actualiza en tiempo real mediante WebSocket.

**Vista de Horarios:** Permite al cuidador consultar, agregar, editar y eliminar horarios de dispensación. Los cambios se envían a la API mediante PUT a `/api/schedules` y se aplican sin reiniciar el servicio.

**Vista de Historial:** Muestra el registro de eventos de dispensación con marca temporal, estado (OK/FAIL) y detalle de si se detectó la extracción del medicamento.

**Control Manual:** Botón que permite ejecutar una dispensación manual enviando POST a `/api/dispense`, útil para pruebas o situaciones de emergencia.

---

## 8. Flujo de Comunicación Dashboard ↔ Hardware

### 8.1 Secuencia de Comunicación

```
  NAVEGADOR (PC)                RASPBERRY PI ZERO 2W                 HARDWARE
  ┌────────────┐               ┌─────────────────────┐              ┌──────────┐
  │ React.js   │               │                     │              │          │
  │ Dashboard  │───── HTTP ───►│  FastAPI (Uvicorn)   │              │          │
  │            │  GET /status  │         │            │              │          │
  │            │◄── JSON ──────│         │            │              │          │
  │            │               │         ▼            │              │          │
  │            │               │  Módulos Python      │              │          │
  │            │── PUT ───────►│  ┌─Scheduler─┐       │              │          │
  │            │ /schedules    │  │ Recarga    │       │              │          │
  │            │◄── 200 OK ────│  │ config     │       │              │          │
  │            │               │  └────────────┘       │              │          │
  │            │               │                      │              │          │
  │            │── POST ──────►│  Controlador Servo ──────── PWM ──►│  SG90    │
  │            │ /dispense     │         │            │              │          │
  │            │               │         ▼            │              │          │
  │            │               │  Gestor Sensores  ◄───── Señal ────│ Sensor IR│
  │            │               │         │            │              │          │
  │            │               │  Sistema Logs        │              │          │
  │            │               │         │            │              │          │
  │            │◄── WS ────────│  WebSocket broadcast │              │          │
  │            │  /ws/status   │         │            │              │          │
  └────────────┘               └─────────────────────┘              └──────────┘
```

### 8.2 Descripción del Flujo

**Flujo de dispensación automática (sin intervención del dashboard):**

1. El Scheduler monitorea continuamente el reloj del sistema.
2. El Controlador del Servo genera la señal PWM en GPIO18 y posiciona el carrusel en el compartimento correspondiente al día actual.
3. El Gestor de Sensores espera la señal de extracción desde GPIO17.
4. Si se detecta la extracción, el evento se registra como OK; si no se detecta dentro del tiempo de espera, se registra como FAIL.
5. El Sistema de Logs guarda el evento con marca temporal UTC.
6. Si no hay conectividad, el Gestor de Tolerancia a Fallos almacena el evento para sincronizarlo cuando se restablezca la red.
7. Si el dashboard está conectado, se emite una actualización por WebSocket.

**Flujo de dispensación manual (desde el dashboard):**

1. El cuidador presiona el botón de dispensación manual en el dashboard.
2. React envía POST a `/api/dispense`.
3. FastAPI invoca el Controlador del Servo.
4. Se ejecuta la misma secuencia de pasos 2 a 7 del flujo automático.

**Flujo de configuración de horarios:**

1. El cuidador modifica los horarios desde la vista de horarios del dashboard.
2. React envía PUT a `/api/schedules` con la nueva configuración.
3. FastAPI persiste la configuración en el archivo local y notifica al Scheduler.
4. El Scheduler recarga la configuración sin reiniciar el servicio.

---

## 9. Estructura de Carpetas del Proyecto

```
healthtech/
├── backend/
│   ├── main.py                  # Punto de entrada FastAPI + Uvicorn
│   ├── requirements.txt         # Dependencias Python
│   ├── config/
│   │   └── schedules.json       # Configuración de horarios
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_schedules.py  # Endpoints de horarios
│   │   ├── routes_status.py     # Endpoint de estado
│   │   ├── routes_logs.py       # Endpoint de historial
│   │   ├── routes_dispense.py   # Endpoint de dispensación manual
│   │   └── websocket.py         # WebSocket de estado en tiempo real
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── scheduler.py         # Planificador de horarios
│   │   ├── servo_controller.py  # Control PWM del SG90
│   │   ├── sensor_manager.py    # Lectura del sensor de peso HX711
│   │   ├── logger.py            # Registro de eventos con timestamp UTC
│   │   └── fault_tolerance.py   # Cola de eventos pendientes
│   └── logs/
│       └── events.log           # Archivo de registro de eventos
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.jsx              # Componente raíz
│       ├── index.js             # Punto de entrada React
│       ├── components/
│       │   ├── StatusView.jsx   # Vista de estado en tiempo real
│       │   ├── ScheduleView.jsx # Vista de gestión de horarios
│       │   ├── LogsView.jsx     # Vista de historial de eventos
│       │   └── ManualDispense.jsx # Botón de dispensación manual
│       └── services/
│           └── api.js           # Cliente HTTP para comunicación con FastAPI
└── docs/
    ├── 00-INDICE-MAESTRO.md
    └── 01-DOCUMENTACION-TECNICA-GENERAL.md
```

---

## 10. Especificación de Requerimientos

### 10.1 Requerimientos Funcionales

| ID   | Descripción                                                                                              |
|------|----------------------------------------------------------------------------------------------------------|
| RF-2 | El sistema debe posicionar automáticamente un carrusel rotativo compuesto por siete compartimentos semanales. |
| RF-3 | El sistema debe detectar la extracción del medicamento mediante sensor IR o capacitivo.                   |
| RF-5 | El sistema debe permitir modificación dinámica de horarios sin reiniciar el servicio.                    |
| RF-6 | El sistema debe registrar todos los eventos con marca temporal UTC.                                       |
| RF-7 | El sistema debe operar aun cuando exista pérdida temporal de conexión a Internet, almacenando notificaciones pendientes. |

### 10.2 Requerimientos No Funcionales

| ID    | Descripción                                                                                   |
|-------|-----------------------------------------------------------------------------------------------|
| RNF-1 | El sistema deberá mantener una disponibilidad mínima del 99.5%.                              |
| RNF-2 | El tiempo entre activación del evento y movimiento del servo no deberá superar 200 ms.       |
| RNF-4 | El software deberá ejecutarse sobre Raspberry Pi OS con Python 3.9 o superior.               |
| RNF-5 | El sistema deberá consumir menos de 5W en estado de espera.                                  |
| RNF-6 | El sistema deberá tolerar fallos temporales de red sin pérdida de eventos.                   |
| RNF-7 | El sistema deberá reiniciar automáticamente servicios críticos ante fallos.                   |

---

## 11. Flujo Operativo del Sistema

### 11.1 Diagrama de Flujo

```
                         ┌─────────┐
                         │ INICIO  │
                         └────┬────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Esperar horario       │◄──────────────────────┐
                  │ programado            │                       │
                  └───────────┬───────────┘                       │
                              │                                   │
                              ▼                                   │
                  ┌───────────────────────┐                       │
                  │ ¿Hora de medicamento? │                       │
                  └───────┬───────┬───────┘                       │
                     NO   │       │  SÍ                           │
                     │    │       │                                │
                     │    │       ▼                                │
                     │    │  ┌──────────────────┐                  │
                     │    │  │ Mover SG90 al    │                  │
                     │    │  │ compartimento    │                  │
                     │    │  │ del día          │                  │
                     │    │  └────────┬─────────┘                  │
                     │    │           │                             │
                     │    │           ▼                             │
                     │    │  ┌──────────────────┐                  │
                     │    │  │ Esperar detección│                  │
                     │    │  │ de extracción    │                  │
                     │    │  └───────┬──┬───────┘                  │
                     │    │         │  │                            │
                     │    │    SÍ   │  │   NO                      │
                     │    │         ▼  ▼                            │
                     │    │  ┌────────┐ ┌──────────┐               │
                     │    │  │Log: OK │ │Log: FAIL │               │
                     │    │  └───┬────┘ └─────┬────┘               │
                     │    │      │            │                    │
                     │    │      └──────┬─────┘                    │
                     │    │             │                           │
                     └────┴─────────────┴─────────────────────────────┘
```

### 11.2 Descripción de la Secuencia

1. El sistema permanece en espera activa, monitoreando el reloj del sistema contra los horarios configurados.
2. El servomotor SG90 recibe la señal PWM y rota el carrusel hasta posicionar el compartimento correspondiente al día actual frente al punto de acceso del usuario.
3. El sistema queda en espera de la señal del sensor IR o capacitivo que confirme que el medicamento fue retirado.
4. Si se detecta la extracción, el evento se registra localmente con estado OK y marca temporal UTC. Si transcurre el tiempo de espera sin detección, se registra como FAIL.
5. El sistema retorna al ciclo de espera.

---

## 12. Dependencias y Comandos de Instalación

### 12.1 Backend (Raspberry Pi)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv python3-lgpio

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
pip install fastapi uvicorn gpiozero lgpio
```

Archivo `requirements.txt`:

```text
fastapi
uvicorn
gpiozero
lgpio
```

### 12.2 Frontend (Máquina de Desarrollo)

```bash
# Crear proyecto React
npx create-react-app healthtech-dashboard
cd healthtech-dashboard

# Instalar dependencias adicionales (si se requieren)
npm install axios
```

### 12.3 Ejecución del Backend

```bash
# Desde la Raspberry Pi, en el directorio backend/
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 12.4 Ejecución del Frontend (Desarrollo)

```bash
# Desde la máquina del desarrollador, en el directorio frontend/
npm start
# Acceder en http://localhost:3000
# Configurar proxy o variable de entorno para apuntar a http://<ip-raspberry>:8000
```

---

## 13. Notas y Limitaciones

- Este documento se basa en el documento de diseño y especificación técnica HealthTech v2.0.0 (mayo 2026), complementado con las decisiones de diseño comunicadas por el equipo del proyecto (uso de SG90, FastAPI, React.js, arquitectura monolítica sin microcontrolador auxiliar).
- Los endpoints de la API y las vistas del dashboard son una especificación mínima derivada de los requerimientos funcionales documentados. No constituyen un contrato de API definitivo.
- Las versiones de las librerías Python y Node.js indicadas son versiones mínimas recomendadas; se debe verificar la compatibilidad con la versión de Raspberry Pi OS instalada.
- Los diagramas ASCII son representaciones simplificadas. Para documentación formal, se recomienda su reemplazo por diagramas generados con herramientas como draw.io, Mermaid o PlantUML.
