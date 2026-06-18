"""
hx711_calibrate.py — Calibración y diagnóstico del sensor de peso HX711.

Ejecutar en la Raspberry Pi Zero 2W con la celda de carga montada y conectada:

  cd /home/<usuario>/Desktop/HealthTech/backend
  python3 scripts/hx711_calibrate.py

Qué hace:
  1. Diagnóstico de estabilidad: toma N lecturas crudas y reporta media y desvío.
     Si el desvío es enorme, el bit-bang de gpiozero está corrompiendo la lectura
     y hay que reescribir _read_hx711_raw() con lgpio directo ANTES de calibrar.
  2. Tara con la bandeja vacía.
  3. Pide colocar un peso de referencia conocido (en gramos).
  4. Calcula CALIBRATION_FACTOR = peso_conocido / delta_crudo y lo PERSISTE
     (logs/hx711_calibration.json) para que sensor_manager lo cargue al arrancar.
  5. Verifica: con el peso aún sobre la balanza, read_weight() debe dar ~peso real.

Por qué importa:
  Sin este paso, CALIBRATION_FACTOR=1.0 y read_weight() devuelve cuentas crudas
  del ADC, no gramos. El umbral DROP_THRESHOLD_G (gramos) no significa nada y la
  detección de extracción (RF-3) no puede funcionar.
"""

from __future__ import annotations

import os
import statistics
import sys
import time

# Add backend root to path so modules can be imported directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.sensor_manager import (  # noqa: E402
    HARDWARE_AVAILABLE,
    HX711_DT_PIN,
    HX711_SCK_PIN,
    CALIBRATION_FILE,
    DROP_THRESHOLD_G,
    tare,
    read_weight,
    read_weight_raw,
    set_calibration_factor,
)

# Number of raw samples for stability diagnostic and for averaging the delta.
SAMPLE_COUNT: int = 30

# Relative-spread threshold: if stdev/|mean| exceeds this, the reading is unstable.
UNSTABLE_RATIO: float = 0.05


def _header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _warn(msg: str) -> None:
    print(f"  [AVISO]  {msg}")


def _fail(msg: str) -> None:
    print(f"  [FALLO]  {msg}")


def _sample_raw(n: int) -> list:
    """Take n tare-corrected raw readings, returning the list."""
    samples = []
    for _ in range(n):
        samples.append(read_weight_raw())
        time.sleep(0.05)
    return samples


def _diagnose_stability() -> bool:
    """Take N raw samples and report mean/stdev. Returns True if stable enough."""
    _header(f"Diagnóstico de estabilidad ({SAMPLE_COUNT} lecturas crudas)")
    print("  No toque la balanza durante la medición...")

    samples = _sample_raw(SAMPLE_COUNT)
    mean = statistics.fmean(samples)
    stdev = statistics.pstdev(samples)

    print(f"  media={mean:,.0f} cuentas   desvío={stdev:,.0f}")

    # A constant reading (stdev≈0) near zero means the sensor isn't responding:
    # DOUT stuck LOW → no data. This is NOT the same as "noisy/unstable".
    if stdev == 0 and abs(mean) < 1000:
        _fail(
            "Lectura CONSTANTE ~0: el HX711 no está entregando datos.\n"
            "  Revise alimentación (VCC 3.3V), GND común y que DT→GPIO17 /\n"
            "  SCK→GPIO23 estén conectados. Ejecute scripts/hx711_lgpio_probe.py."
        )
        return False

    # Relative spread only makes sense away from zero.
    spread = abs(stdev / mean) if abs(mean) >= 1000 else 0.0
    if spread > UNSTABLE_RATIO:
        _warn(
            f"Lecturas RUIDOSAS (spread={spread:.2%}). Promedie más muestras o\n"
            "  verifique el montaje mecánico de la celda de carga."
        )
        return False

    _ok("Lecturas estables. Se puede calibrar con confianza.")
    return True


def _calibrate() -> None:
    _header("Calibración del HX711")

    input("  >>> Retire todo peso de la bandeja y presione ENTER para TARAR...")
    tare()
    _ok("Tara completada (bandeja vacía = 0).")

    raw_str = input(
        "\n  >>> Coloque un peso de referencia conocido sobre la bandeja.\n"
        "      Ingrese su valor en gramos (ej. 50) y presione ENTER: "
    ).strip()

    try:
        known_grams = float(raw_str)
        if known_grams <= 0:
            raise ValueError
    except ValueError:
        _fail(f"Valor inválido: {raw_str!r}. Debe ser un número mayor que cero.")
        return

    print(f"  Midiendo {SAMPLE_COUNT} lecturas con el peso colocado...")
    deltas = _sample_raw(SAMPLE_COUNT)
    raw_delta = statistics.fmean(deltas)

    if raw_delta == 0:
        _fail(
            "El delta crudo es 0 — el sensor no detecta el peso.\n"
            "  Verifique conexiones y que el peso esté realmente sobre la celda."
        )
        return

    factor = known_grams / raw_delta
    set_calibration_factor(factor)

    _ok(f"CALIBRATION_FACTOR = {factor:.8g}")
    _ok(f"Persistido en: {CALIBRATION_FILE}")

    measured = read_weight()
    error = abs(measured - known_grams)
    print(
        f"\n  Verificación: peso conocido={known_grams:.1f} g  →  "
        f"read_weight()={measured:.1f} g  (error={error:.2f} g)"
    )
    if error <= max(1.0, known_grams * 0.05):
        _ok("Calibración verificada.")
    else:
        _warn("Error de calibración alto. Repita con el sensor estabilizado.")

    print(
        f"\n  Umbral de dispensación actual: DROP_THRESHOLD_G={DROP_THRESHOLD_G} g.\n"
        "  Ajústelo al peso de la pastilla más liviana de su formulario."
    )


def main() -> None:
    print("\n" + "=" * 60)
    print("  HealthTech — Calibración del sensor HX711")
    print("=" * 60)
    print(f"  HX711 DT=GPIO{HX711_DT_PIN}  SCK=GPIO{HX711_SCK_PIN}")

    if not HARDWARE_AVAILABLE:
        _fail(
            "gpiozero no disponible — este script debe correr en la Raspberry Pi\n"
            "  con el hardware conectado. En PC de desarrollo no hay nada que calibrar."
        )
        sys.exit(1)

    try:
        _diagnose_stability()
        _calibrate()
    except KeyboardInterrupt:
        print("\n\n  Calibración interrumpida por el usuario (Ctrl+C).")

    print("\n  Calibración finalizada.\n")


if __name__ == "__main__":
    main()
