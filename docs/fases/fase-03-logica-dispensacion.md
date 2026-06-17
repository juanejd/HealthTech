# Fase 03 — Lógica de Dispensación

## Descripción

Implementa el núcleo funcional del sistema: el planificador de horarios (Scheduler), el motor de síntesis de voz (TTS) y el gestor de tolerancia a fallos para notificaciones pendientes. Esta fase orquesta la secuencia completa de dispensación automática sin intervención del usuario.

## Objetivo

Tener el flujo de dispensación automática completamente funcional: detección de horario → alerta TTS → movimiento del servo → detección de extracción → registro del evento → encolado de notificación.

---

## Módulos y Archivos

| Archivo                                  | Responsabilidad                                                        |
|------------------------------------------|------------------------------------------------------------------------|
| `backend/modules/scheduler.py`           | Monitorea el reloj y dispara eventos en los horarios configurados      |
| `backend/modules/tts_engine.py`          | Síntesis de voz mediante `espeak-ng` o Piper TTS                       |
| `backend/modules/fault_tolerance.py`     | Cola de notificaciones pendientes cuando no hay conexión a Internet    |

---

## Flujo de Dispensación Automática

```
Scheduler detecta horario
        │
        ▼
TTS reproduce alerta (≥60 s antes)
        │
        ▼
servo_controller.move_to_compartment(day_index)
        │
        ▼
sensor_manager.wait_for_extraction(timeout)
        │
   ┌────┴────┐
  True     False
   │         │
Log: OK   Log: FAIL
   │         │
   └────┬────┘
        ▼
fault_tolerance.enqueue(notification)
```

---

## Requerimientos que Cubre

| ID    | Descripción                                                                                              |
|-------|----------------------------------------------------------------------------------------------------------|
| RF-1  | El sistema debe emitir alerta de voz al menos 60 segundos antes de la dispensación programada.           |
| RF-5  | El sistema debe permitir modificación dinámica de horarios sin reiniciar el servicio.                    |
| RF-6  | El sistema debe registrar todos los eventos con marca temporal UTC.                                       |
| RF-7  | El sistema debe operar aun cuando exista pérdida temporal de Internet, almacenando notificaciones pendientes. |
| RNF-1 | Disponibilidad mínima del 99.5%.                                                                         |
| RNF-2 | Tiempo entre activación del evento y movimiento del servo ≤ 200 ms.                                     |
| RNF-6 | El sistema debe tolerar fallos temporales de red sin pérdida de eventos.                                  |
| RNF-7 | El sistema debe reiniciar automáticamente servicios críticos ante fallos.                                 |

---

## Criterios de Aceptación

### Scheduler
- [ ] Lee `config/schedules.json` al arrancar y lo recarga en caliente sin reiniciar el proceso cuando el archivo cambia.
- [ ] Dispara el evento TTS al menos 60 segundos antes de la hora de dispensación configurada.
- [ ] Dispara la dispensación exactamente a la hora configurada (tolerancia ±1 segundo).
- [ ] Soporta múltiples horarios diarios y horarios con días específicos de la semana.
- [ ] Ignora horarios con `enabled: false`.

### TTS Engine
- [ ] Reproduce el mensaje de voz configurado en el horario.
- [ ] Funciona con `espeak-ng` como motor primario.
- [ ] Funciona en modo silencioso (sin audio) cuando no hay dispositivo de audio — para desarrollo.
- [ ] No bloquea el hilo principal del Scheduler (ejecución asíncrona o en hilo separado).

### Fault Tolerance
- [ ] Encola notificaciones cuando no hay conectividad.
- [ ] Reenvía notificaciones encoladas automáticamente al restaurarse la conexión.
- [ ] Persiste la cola en disco para sobrevivir reinicios del sistema.
- [ ] La cola no crece indefinidamente — define una política de retención máxima.

---

## Dependencias

- **Fase 01** — logging y configuración.
- **Fase 02** — `servo_controller` y `sensor_manager`.

---

## Instalación del Motor TTS

```bash
# En la Raspberry Pi
sudo apt install -y espeak-ng

# Verificar
espeak-ng "Es hora de tomar su medicamento."
```

---

## Notas Técnicas

- El Scheduler debe usar el reloj del sistema en UTC internamente y convertir a hora local solo para la interfaz de usuario.
- La recarga dinámica de `schedules.json` puede implementarse con `watchdog` (inotify) o polling periódico (cada 30 s). El polling es más simple y suficiente para este caso.
- `fault_tolerance.py` debe usar una cola persistida en disco (archivo JSON o SQLite) para no perder notificaciones ante reinicios. Un archivo `backend/logs/pending_notifications.json` es suficiente.
- Para RNF-7 (reinicio automático), configurar `systemd` con `Restart=always` en la unidad de servicio — no es responsabilidad del código Python.
