# Fase 06 — Frontend Dashboard (React.js)

## Descripción

Implementa el dashboard web que el cuidador usa desde cualquier navegador en la red local. La aplicación React.js se conecta a la API FastAPI de la Raspberry Pi y presenta cuatro vistas funcionales: estado en tiempo real, gestión de horarios, historial de eventos y dispensación manual.

## Objetivo

El cuidador puede monitorear el sistema, modificar horarios, revisar el historial de eventos y activar una dispensación manual desde cualquier dispositivo con navegador en la red local, sin necesidad de instalar ninguna app.

---

## Archivos del Proyecto

| Archivo                              | Responsabilidad                                                     |
|--------------------------------------|---------------------------------------------------------------------|
| `frontend/src/App.jsx`               | Componente raíz con routing y navegación entre vistas               |
| `frontend/src/index.js`              | Punto de entrada React                                               |
| `frontend/src/services/api.js`       | Cliente HTTP que abstrae todas las llamadas a la API FastAPI         |
| `frontend/src/components/StatusView.jsx`    | Vista de estado en tiempo real (WebSocket)                   |
| `frontend/src/components/ScheduleView.jsx`  | Vista de gestión de horarios (CRUD)                          |
| `frontend/src/components/LogsView.jsx`      | Vista de historial de eventos                                |
| `frontend/src/components/ManualDispense.jsx`| Botón de dispensación manual                                 |

---

## Vistas

### StatusView
- Muestra: día activo, compartimento actual, próximo evento, estado de conectividad Wi-Fi y Telegram, resultado del último evento (OK/FAIL).
- Se actualiza en tiempo real mediante WebSocket (`/ws/status`).
- Indicadores visuales de color: verde = OK, rojo = FAIL/desconectado.

### ScheduleView
- Lista todos los horarios configurados.
- Permite agregar, editar y eliminar horarios.
- Envía cambios con PUT a `/api/schedules` — los cambios se aplican sin reiniciar el sistema.
- Campos por horario: hora (`HH:MM`), días de la semana (checkbox), mensaje personalizado, habilitado/deshabilitado.

### LogsView
- Tabla de eventos ordenados cronológicamente (más reciente primero).
- Columnas: timestamp, estado (OK/FAIL), extracción detectada (Sí/No), día de la semana.
- Paginación o scroll infinito para historiales largos.

### ManualDispense
- Botón único "Dispensar ahora".
- Muestra estado de carga mientras se ejecuta.
- Muestra resultado (OK/FAIL) al completar.
- Requiere confirmación antes de ejecutar — evita activaciones accidentales.

---

## Requerimientos que Cubre

| ID    | Descripción                                                       |
|-------|-------------------------------------------------------------------|
| RF-5  | Modificación dinámica de horarios sin reiniciar el servicio.      |
| RF-6  | Historial de eventos consultable desde el dashboard.              |

---

## Criterios de Aceptación

- [ ] La aplicación carga en `http://localhost:3000` (desarrollo) sin errores en consola.
- [ ] `StatusView` muestra datos actualizados sin recargar la página (WebSocket funcional).
- [ ] `ScheduleView` persiste cambios de horarios y el Scheduler los refleja dentro de 30 segundos.
- [ ] `LogsView` muestra todos los eventos con timestamps correctos en formato legible.
- [ ] `ManualDispense` muestra un diálogo de confirmación antes de enviar `POST /api/dispense`.
- [ ] La aplicación funciona en Chrome y Firefox modernos.
- [ ] En mobile (viewport < 768px), la interfaz es usable (responsive mínimo).
- [ ] El cliente HTTP de `api.js` apunta a la URL de la Raspberry Pi configurable por variable de entorno (`REACT_APP_API_URL`).

---

## Dependencias

- **Fase 05** — API backend completamente funcional.

---

## Configuración del Proxy de Desarrollo

En desarrollo, el frontend corre en `localhost:3000` y la API en `<rpi-ip>:8000`. Configurar `REACT_APP_API_URL` en `.env.local`:

```bash
# frontend/.env.local
REACT_APP_API_URL=http://192.168.1.100:8000
```

En `api.js`:

```js
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

---

## Instalación y Ejecución

```bash
# Crear proyecto
npx create-react-app healthtech-dashboard
cd healthtech-dashboard

# Instalar dependencias adicionales
npm install axios

# Iniciar servidor de desarrollo
npm start
```

---

## Notas Técnicas

- Usar el hook nativo `useEffect` con `WebSocket` para la conexión de tiempo real en `StatusView` — no se requieren librerías externas.
- El cliente HTTP (`api.js`) puede usar `fetch` nativo o `axios`. `axios` simplifica el manejo de errores y headers.
- Para el MVP no se requiere routing de múltiples páginas — las vistas pueden ser tabs dentro de un único componente `App`.
- No usar `create-react-app` si el proyecto ya tiene Vite configurado. Preferir Vite para proyectos nuevos por su velocidad de compilación.
