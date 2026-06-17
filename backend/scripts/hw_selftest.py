#!/usr/bin/env python3
"""
hw_selftest.py — Prueba de hardware para el dispensador de medicamentos HealthTech.

Ejecutar en la Raspberry Pi Zero 2W con todo el hardware conectado:

  sudo systemctl enable --now pigpiod
  cd /home/<usuario>/Desktop/HealthTech/backend
  python3 scripts/hw_selftest.py

Requisitos previos:
  pip install gpiozero pigpio

El script realiza las siguientes pruebas de forma secuencial:
  (a) Prueba del servo FS90R: gira 1 segundo y detiene.
  (b) Lectura continua del HX711: muestra el peso en pantalla.
  (c) Un paso de 45° con el servo y confirmación de peso.
  (d) Limpieza de GPIO y salida.

Cableado validado:
  FS90R señal  → GPIO18 (BCM)
  HX711 DT     → GPIO17 (BCM)
  HX711 SCK    → GPIO23 (BCM)
  FS90R VCC    → 5V (pin físico 2)
  HX711 VCC    → 3.3V (pin físico 1)
  GND común
"""
from __future__ import annotations

import sys
import time
import os

# Add backend root to path so modules can be imported directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.servo_controller import (
    HARDWARE_AVAILABLE as SERVO_HW,
    stop,
    step_one_compartment,
    set_home,
    get_position,
    cleanup as servo_cleanup,
    STEP_DURATION_S,
    STEP_SPEED,
    DIRECTION,
    SERVO_GPIO_PIN,
    _get_servo,
)
from modules.sensor_manager import (
    HARDWARE_AVAILABLE as SENSOR_HW,
    HX711_DT_PIN,
    HX711_SCK_PIN,
    tare,
    read_weight,
    wait_for_dispense_confirmation,
    DROP_THRESHOLD_G,
    CALIBRATION_FACTOR,
)


def _header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _warn(msg: str) -> None:
    print(f"  [AVISO]  {msg}")


def _fail(msg: str) -> None:
    print(f"  [FALLO]  {msg}")


def _check_hardware() -> bool:
    _header("Verificación de hardware disponible")

    if not SERVO_HW:
        _fail(
            "gpiozero/pigpio no encontrado. "
            "Instale con: pip install gpiozero pigpio\n"
            "  y ejecute: sudo systemctl enable --now pigpiod"
        )
        return False

    _ok(f"gpiozero disponible — servo en GPIO{SERVO_GPIO_PIN}")
    _ok(f"HX711 DT=GPIO{HX711_DT_PIN}  SCK=GPIO{HX711_SCK_PIN}")
    return True


def _test_servo_spin() -> None:
    """(a) Girar el servo 1 segundo, luego detener."""
    _header("Prueba (a): Giro del servo FS90R (1 segundo)")

    print(
        f"  Configuración: velocidad={STEP_SPEED}, "
        f"dirección={DIRECTION:+.1f}, GPIO{SERVO_GPIO_PIN}"
    )
    print("  Girando el servo durante 1 segundo...")

    try:
        servo = _get_servo()
        if servo is None:
            _fail("No se pudo crear el objeto Servo. ¿Está pigpiod en ejecución?")
            return

        servo.value = STEP_SPEED * DIRECTION
        time.sleep(1.0)
        servo.value = 0.0  # detener (neutral)
        time.sleep(0.1)
        servo.detach()
        servo.close()
        _ok("Servo giró y detuvo correctamente.")
        print(
            "\n  >>> ¿El carrusel giró hacia adelante?\n"
            "      Si giró al revés, cambie DIRECTION = -1.0 en servo_controller.py"
        )
    except Exception as exc:
        _fail(f"Error al mover el servo: {exc}")


def _test_hx711_continuous() -> None:
    """(b) Lectura continua del HX711 durante 5 segundos."""
    _header("Prueba (b): Lectura continua del HX711 (5 segundos)")
    print(f"  Factor de calibración actual: CALIBRATION_FACTOR={CALIBRATION_FACTOR}")
    print("  Tarar balanza (asegúrese que la bandeja esté vacía)...")
    tare()
    _ok("Tara completada.")

    print("  Lecturas de peso (5 segundos). Coloque y retire pesos para verificar:\n")
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        w = read_weight()
        bar_len = max(0, min(40, int(w / 5)))
        bar = "#" * bar_len
        print(f"    {w:+8.1f} g  |{bar:<40}|", end="\r")
        time.sleep(0.2)

    print()
    _ok("Lectura del sensor completada.")
    print(
        "\n  Si el peso no es ~0 g con la bandeja vacía:\n"
        "    1. Llame tare() nuevamente.\n"
        "    2. Si el valor oscila mucho, verifique conexiones HX711.\n"
        f"\n  Para calibrar con un peso conocido W_g:\n"
        f"    CALIBRATION_FACTOR = W_g / read_weight_raw()"
    )


def _test_one_step_with_confirmation() -> None:
    """(c) Un paso de 45° + confirmación de peso."""
    _header("Prueba (c): Un paso del carrusel (45°) + confirmación HX711")

    print(f"  Duración del paso actual: STEP_DURATION_S={STEP_DURATION_S:.3f} s")
    print("  Posición inicial del carrusel:", get_position())
    print()
    input("  >>> Presione ENTER para ejecutar un paso de 45°...")

    try:
        step_one_compartment()
        _ok(f"Paso completado. Posición ahora: {get_position()}")
    except Exception as exc:
        _fail(f"Error en el paso del servo: {exc}")
        return

    print(
        f"\n  Esperando confirmación de dispensación "
        f"(umbral={DROP_THRESHOLD_G} g, timeout=10 s)..."
    )
    confirmed = wait_for_dispense_confirmation(timeout_seconds=10, drop_threshold=DROP_THRESHOLD_G)

    if confirmed:
        _ok("¡Dispensación confirmada por el sensor de peso!")
    else:
        _warn(
            "No se detectó caída de peso suficiente dentro del tiempo límite.\n"
            f"  Ajuste DROP_THRESHOLD_G (actual={DROP_THRESHOLD_G} g) en sensor_manager.py\n"
            "  o verifique que el medicamento cayó en la bandeja."
        )

    print(
        "\n  Si el paso NO fue de ~45°:\n"
        f"    - Aumente STEP_DURATION_S si giró menos (actual={STEP_DURATION_S:.3f} s)\n"
        f"    - Disminuya STEP_DURATION_S si giró más\n"
        "    - Edite el valor en backend/modules/servo_controller.py"
    )


def _cleanup() -> None:
    _header("Limpieza de GPIO")
    servo_cleanup()
    _ok("GPIO liberado correctamente.")


def main() -> None:
    print("\n" + "="*60)
    print("  HealthTech — Autoprueba de Hardware (hw_selftest.py)")
    print("="*60)
    print("  Plataforma objetivo: Raspberry Pi Zero 2W")
    print("  Ejecute este script directamente en la Pi con hardware conectado.")
    print()

    ok = _check_hardware()
    if not ok:
        print(
            "\nEste script debe ejecutarse en la Raspberry Pi con "
            "gpiozero y pigpio instalados.\n"
        )
        sys.exit(1)

    try:
        _test_servo_spin()
        _test_hx711_continuous()
        _test_one_step_with_confirmation()
    except KeyboardInterrupt:
        print("\n\n  Prueba interrumpida por el usuario (Ctrl+C).")
    finally:
        _cleanup()

    print("\n  Autoprueba finalizada.\n")


if __name__ == "__main__":
    main()
