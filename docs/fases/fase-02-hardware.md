# Fase 02 — Capa de Control de Hardware

## Descripción

Implementa los módulos Python que abstraen el acceso a los periféricos físicos: el servomotor SG90 (carrusel semanal), el sensor IR de extracción y el pulsador de confirmación manual. Esta fase requiere una Raspberry Pi Zero 2W con los componentes conectados según la asignación de pines documentada.

## Objetivo

Disponer de una API Python limpia que permita a la lógica de negocio (Fase 03) controlar el hardware sin conocer los detalles de GPIO o PWM.

---

## Módulos y Archivos

| Archivo                              | Responsabilidad                                              |
|--------------------------------------|--------------------------------------------------------------|
| `backend/modules/servo_controller.py` | Genera señal PWM en GPIO18 para posicionar el carrusel SG90 |
| `backend/modules/sensor_manager.py`   | Lee sensor IR (GPIO17) y pulsador (GPIO27)                   |

---

## Interfaz de Pines GPIO

| GPIO   | Componente    | Función                              |
|--------|---------------|--------------------------------------|
| GPIO18 | SG90          | Señal PWM del servomotor (50 Hz)     |
| GPIO17 | Sensor IR     | Detección de extracción del medicamento |
| GPIO27 | Pulsador      | Confirmación manual o mantenimiento  |

---

## Lógica del Servomotor SG90

El carrusel tiene 7 compartimentos, uno por día. El ángulo entre compartimentos es:

```
θ = 360° / 7 ≈ 51.43°
```

El mapeo de ángulo a pulso PWM (frecuencia 50 Hz):

| Posición | Pulso   |
|----------|---------|
| 0°       | ~0.5 ms |
| 90°      | ~1.5 ms |
| 180°     | ~2.5 ms |

El compartimento del día actual se calcula a partir del día de la semana (lunes = 0, domingo = 6).

---

## Requerimientos que Cubre

| ID    | Descripción                                                                              |
|-------|------------------------------------------------------------------------------------------|
| RF-2  | El sistema debe posicionar automáticamente el carrusel de siete compartimentos semanales. |
| RF-3  | El sistema debe detectar la extracción del medicamento mediante sensor IR o capacitivo.  |
| RNF-2 | El tiempo entre activación del evento y movimiento del servo no debe superar 200 ms.    |

---

## Criterios de Aceptación

- [ ] `servo_controller.py` expone una función `move_to_compartment(day_index: int)` que posiciona el carrusel en el compartimento correcto.
- [ ] El movimiento del servo se completa en menos de 200 ms desde la invocación (RNF-2).
- [ ] `sensor_manager.py` expone `wait_for_extraction(timeout_seconds: int) -> bool` que retorna `True` si detecta extracción o `False` si se agota el tiempo.
- [ ] `sensor_manager.py` expone `read_button() -> bool` para lectura del pulsador.
- [ ] Los pines GPIO se liberan correctamente al terminar (`GPIO.cleanup()`).
- [ ] Los módulos funcionan en modo simulado (mock) cuando no se detecta hardware GPIO — para desarrollo en PC.

---

## Dependencias

- **Fase 01** completada (estructura de proyecto y entorno virtual).

---

## Modo Simulado (Desarrollo sin Hardware)

Para permitir desarrollo y testing en máquinas sin GPIO, los módulos deben detectar si `RPi.GPIO` está disponible. Si no lo está, operan en modo mock:

```python
try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    HARDWARE_AVAILABLE = False
```

En modo mock, `move_to_compartment` loguea el movimiento simulado y `wait_for_extraction` retorna `True` después de un delay configurable.

---

## Comandos de Verificación

```bash
# Test manual del servo (en la RPi con hardware conectado)
python3 -c "from modules.servo_controller import move_to_compartment; move_to_compartment(0)"

# Test del sensor IR
python3 -c "from modules.sensor_manager import wait_for_extraction; print(wait_for_extraction(10))"
```

---

## Notas Técnicas

- Usar `RPi.GPIO` en modo BCM (`GPIO.setmode(GPIO.BCM)`).
- El SG90 puede alimentarse desde el pin 5V de la RPi en carga ligera. Ante comportamiento errático del servo, usar fuente externa dedicada de 5V.
- El pulsador debe configurarse con resistencia pull-down (`GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)`).
