"""
hx711_lgpio_probe.py — Probe de diagnóstico: lee el HX711 con lgpio DIRECTO.

NO toca el código de producción. Su único propósito es decidir una hipótesis:

  ¿El 0 constante que devuelve sensor_manager viene del driver gpiozero (lento)
  o de un problema de cableado/alimentación?

Si este probe devuelve valores REALES y variables  → el cableado está bien y el
  problema es gpiozero. Hay que reescribir _read_hx711_raw() con lgpio.
Si este probe TAMBIÉN devuelve 0 / valores fijos    → revisar alimentación (VCC
  3.3V), GND común, y que DT→GPIO17 / SCK→GPIO23 estén realmente conectados.

Ejecutar en la Raspberry Pi:
  cd /home/<usuario>/Desktop/HealthTech/backend
  python3 scripts/hx711_lgpio_probe.py
"""

from __future__ import annotations

import sys
import time

try:
    import lgpio
except ImportError:
    print(
        "[FALLO] lgpio no está instalado. En la Pi: sudo apt install -y python3-lgpio"
    )
    sys.exit(1)

DT_PIN = 17  # BCM — HX711 DOUT
SCK_PIN = 23  # BCM — HX711 PD_SCK
GPIO_CHIP = 0
SAMPLES = 10
DRDY_TIMEOUT_S = 1.0


def read_raw(handle: int) -> "int | None":
    """One 24-bit read via direct lgpio bit-bang. None on DRDY timeout."""
    # Wait for data ready: HX711 holds DOUT HIGH until a conversion is ready.
    deadline = time.monotonic() + DRDY_TIMEOUT_S
    while lgpio.gpio_read(handle, DT_PIN) == 1:
        if time.monotonic() > deadline:
            return None  # honest failure — no masking with a fake value
        time.sleep(0.001)

    raw = 0
    for _ in range(24):
        lgpio.gpio_write(handle, SCK_PIN, 1)
        bit = lgpio.gpio_read(handle, DT_PIN)
        lgpio.gpio_write(handle, SCK_PIN, 0)
        raw = (raw << 1) | bit

    # 25th pulse selects channel A, gain 128 for the next conversion.
    lgpio.gpio_write(handle, SCK_PIN, 1)
    lgpio.gpio_write(handle, SCK_PIN, 0)

    # Two's-complement for 24-bit signed.
    if raw & 0x800000:
        raw -= 0x1000000
    return raw


def main() -> None:
    print("=" * 60)
    print("  Probe HX711 vía lgpio DIRECTO")
    print(f"  DT=GPIO{DT_PIN}  SCK=GPIO{SCK_PIN}  chip={GPIO_CHIP}")
    print("=" * 60)

    handle = lgpio.gpiochip_open(GPIO_CHIP)
    try:
        lgpio.gpio_claim_input(handle, DT_PIN)
        lgpio.gpio_claim_output(handle, SCK_PIN, 0)  # SCK starts LOW
        time.sleep(0.1)

        values = []
        for i in range(SAMPLES):
            raw = read_raw(handle)
            if raw is None:
                print(
                    f"  [{i + 1:2d}] DRDY timeout — DOUT nunca bajó (chip sin responder)"
                )
            else:
                print(f"  [{i + 1:2d}] raw = {raw:,}")
                values.append(raw)
            time.sleep(0.1)

        print("-" * 60)
        if not values:
            print(
                "  VEREDICTO: no se obtuvo ninguna lectura. Revisar alimentación y cableado."
            )
        elif len(set(values)) == 1:
            print(
                f"  VEREDICTO: valor FIJO ({values[0]:,}). No es señal real — revisar cableado/GND."
            )
        else:
            lo, hi = min(values), max(values)
            print(f"  VEREDICTO: lecturas REALES y variables (rango {lo:,} … {hi:,}).")
            print("  → El cableado está bien. El driver gpiozero es el problema.")
            print("  → Reescribir _read_hx711_raw() en sensor_manager.py con lgpio.")
    finally:
        lgpio.gpiochip_close(handle)
        print("\n  GPIO liberado.")


if __name__ == "__main__":
    main()
