# Fase 04 — Módulo de Comunicación Telegram

## Descripción

Implementa el bot de Telegram que notifica al cuidador sobre cada evento de dispensación. Se integra con el módulo de tolerancia a fallos (Fase 03) para garantizar entrega eventual de notificaciones aun sin conectividad inmediata.

## Objetivo

El cuidador recibe una notificación Telegram dentro de los 30 segundos posteriores a cada evento de dispensación, con información del estado (OK/FAIL) y si se detectó extracción del medicamento.

---

## Módulos y Archivos

| Archivo                              | Responsabilidad                                               |
|--------------------------------------|---------------------------------------------------------------|
| `backend/modules/telegram_bot.py`    | Envío de notificaciones al cuidador vía Telegram Bot API     |

---

## Formato de Notificación

Mensaje mínimo que debe enviarse al cuidador:

```
✅ Medicamento dispensado — Lunes 16/06/2026 08:00 UTC
Estado: OK
Extracción detectada: Sí
```

```
⚠️ Medicamento dispensado — Lunes 16/06/2026 08:00 UTC
Estado: FAIL
Extracción detectada: No (timeout)
```

---

## Requerimientos que Cubre

| ID    | Descripción                                                                                             |
|-------|---------------------------------------------------------------------------------------------------------|
| RF-4  | El sistema debe enviar notificación por Telegram al cuidador en menos de 30 segundos tras la dispensación. |
| RF-7  | Las notificaciones deben encolarse si no hay conectividad y enviarse al restaurarse la red.             |
| RNF-3 | Las credenciales del bot deben almacenarse en variables de entorno.                                     |

---

## Criterios de Aceptación

- [ ] `telegram_bot.py` expone `send_notification(event: dict) -> bool` que retorna `True` si el envío fue exitoso.
- [ ] El tiempo entre la dispensación y el envío de la notificación es inferior a 30 segundos (RF-4).
- [ ] Las credenciales se leen exclusivamente de variables de entorno `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` — nunca hardcodeadas.
- [ ] Si el envío falla (sin red, timeout), delega a `fault_tolerance.enqueue()` y retorna `False`.
- [ ] Cuando `fault_tolerance` tiene notificaciones pendientes, `telegram_bot` las procesa en orden FIFO al detectar conectividad restaurada.
- [ ] El módulo es testeable en modo mock sin hacer llamadas reales a la API de Telegram.

---

## Variables de Entorno Requeridas

```bash
TELEGRAM_BOT_TOKEN=7xxxxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-100xxxxxxxxxx
```

Agregar al archivo `.env.example` del proyecto.

---

## Dependencias

- **Fase 01** — logging y variables de entorno.
- **Fase 03** — `fault_tolerance.py` para encolamiento de mensajes pendientes.

---

## Instalación

```bash
pip install python-telegram-bot
```

---

## Comandos de Verificación

```bash
# Test de envío directo (requiere credenciales reales en .env)
python3 -c "
from modules.telegram_bot import send_notification
result = send_notification({
    'timestamp': '2026-06-16T08:00:00Z',
    'status': 'OK',
    'extraction_detected': True,
    'day': 'lunes'
})
print('Enviado:', result)
"
```

---

## Notas Técnicas

- Usar `python-telegram-bot` en modo asíncrono (`asyncio`) para no bloquear el hilo del Scheduler.
- El endpoint de la Bot API es `https://api.telegram.org/bot{token}/sendMessage`.
- Configurar un timeout de red de 10 segundos para las llamadas HTTP — evita que un fallo de red bloquee el flujo de dispensación.
- El `TELEGRAM_CHAT_ID` puede ser el ID de un usuario o de un grupo. Para grupos, el ID es negativo.
