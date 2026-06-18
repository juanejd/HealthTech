"""
servo_calibrate.py — Script interactivo para calibrar la duración del paso del servo FS90R.

Permite probar diferentes tiempos de giro en segundos para encontrar exactamente
cuánto tiempo se necesita para girar 45° de forma confiable.
Una vez encontrado el valor, tenés que copiarlo en STEP_DURATION_S dentro de servo_controller.py.
"""

from __future__ import annotations

import sys
import time
import os

# Agrega la raíz del backend al path para poder importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.servo_controller import (
    HARDWARE_AVAILABLE,
    STEP_SPEED,
    DIRECTION,
    STOP_VALUE,
    _get_servo,
    cleanup,
)


def main() -> None:
    print("\n" + "=" * 60)
    print("  Calibrador Manual de Servo FS90R")
    print("=" * 60)

    if not HARDWARE_AVAILABLE:
        print("\n[ERROR] Hardware (gpiozero/pigpio) no disponible.")
        sys.exit(1)

    print("Este script gira el motor usando la velocidad y dirección de")
    print("servo_controller.py, pero dejándote ingresar el TIEMPO a mano.")
    print("Ideal para encontrar el valor exacto para girar 45°.\n")

    while True:
        try:
            val_str = input(
                "Ingresá el tiempo a girar en segundos (ej: 0.25) o 'q' para salir: "
            ).strip()
            if val_str.lower() in ("q", "quit", "exit"):
                break

            duration = float(val_str)
            if duration <= 0:
                print("  -> El tiempo debe ser mayor a 0.\n")
                continue

            print(f"  -> Girando por {duration} segundos...")
            servo = _get_servo()
            if servo is None:
                print("  -> [ERROR] No se pudo conectar al servo.")
                continue

            servo.value = STEP_SPEED * DIRECTION
            time.sleep(duration)
            servo.value = STOP_VALUE
            time.sleep(0.05)
            servo.detach()
            servo.close()

            print("  -> ¡Giro completado!\n")
            print("     Si giró exactamente 45°, copiá este valor y ponelo")
            print("     como STEP_DURATION_S en servo_controller.py\n")

        except ValueError:
            print("  -> Por favor, ingresá un número válido usando punto (ej: 0.25).\n")
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"  -> [ERROR] Inesperado: {e}")
            break

    cleanup()
    print("Saliendo del calibrador...")


if __name__ == "__main__":
    main()
