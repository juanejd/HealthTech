"""
sensor_manager.py — HX711 load-cell amplifier driver.

Hardware: HX711 connected to:
  DT  (data)  → GPIO17 (BCM)
  SCK (clock) → GPIO23 (BCM)
  VCC → 3.3 V, GND → common GND with Pi

Dispense confirmation logic:
  After the servo positions the carousel, read the load cell.  If the weight
  DROPS by at least drop_threshold grams within timeout_seconds, a pill has
  fallen into the dispensing cup (dispensed = OK).

Pi setup (run once on the Pi):
  sudo systemctl enable --now pigpiod
  pip install gpiozero pigpio

Calibration:
  1. Call tare() with the empty dispensing cup on the scale.
  2. Place a known reference weight and read read_weight().
  3. Set CALIBRATION_FACTOR = known_weight_grams / raw_delta.
  4. Adjust DROP_THRESHOLD_G to match the lightest pill in your formulary.

The HX711 is bit-banged using RPi.GPIO or gpiozero.  To avoid a flaky
third-party lib dependency, a minimal software bit-bang implementation is
provided that operates directly on the GPIO pins.  If gpiozero is not
available (dev PC), the module operates in mock mode.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hardware import guard
# ---------------------------------------------------------------------------

try:
    import gpiozero
    from gpiozero.pins.pigpio import PiGPIOFactory
    from gpiozero import DigitalInputDevice, DigitalOutputDevice

    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    HARDWARE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Pin assignments (BCM)
# ---------------------------------------------------------------------------

HX711_DT_PIN: int = 17   # data
HX711_SCK_PIN: int = 23  # clock

# ---------------------------------------------------------------------------
# Calibration constants — tune on real hardware
# ---------------------------------------------------------------------------

# Multiply raw 24-bit reading by this factor to get grams.
# Compute as: CALIBRATION_FACTOR = known_weight_g / raw_reading_at_known_weight
CALIBRATION_FACTOR: float = 1.0

# Default drop threshold (grams): weight must drop by this much to confirm
# a dispense.  Tune to the lightest pill in the formulary.
DROP_THRESHOLD_G: float = 5.0

# How often to poll the HX711 during wait_for_dispense_confirmation (seconds).
POLL_INTERVAL_S: float = 0.05

# ---------------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------------

_tare_offset: float = 0.0

# ---------------------------------------------------------------------------
# Internal HX711 bit-bang read
# ---------------------------------------------------------------------------

_MOCK_RAW_VALUE: float = 500000.0  # stable mock raw reading


def _read_hx711_raw() -> float:
    """
    Read a 24-bit value from the HX711 via software bit-bang.

    Returns the signed 24-bit integer (two's complement) from the ADC.
    In mock mode, returns a stable constant.
    """
    if not HARDWARE_AVAILABLE:
        return _MOCK_RAW_VALUE

    try:
        factory = PiGPIOFactory()
        dt = DigitalInputDevice(HX711_DT_PIN, pin_factory=factory)
        sck = DigitalOutputDevice(HX711_SCK_PIN, pin_factory=factory)

        # Wait for DRDY (DT goes LOW when data is ready)
        deadline = time.monotonic() + 1.0
        while dt.value == 1:
            if time.monotonic() > deadline:
                logger.warning("HX711: DRDY timeout — sensor may be offline")
                return _MOCK_RAW_VALUE
            time.sleep(0.001)

        # Clock in 24 bits (MSB first)
        raw: int = 0
        for _ in range(24):
            sck.on()
            time.sleep(0.000001)
            bit = dt.value
            sck.off()
            time.sleep(0.000001)
            raw = (raw << 1) | bit

        # 25th pulse — sets gain to 128 for next reading
        sck.on()
        time.sleep(0.000001)
        sck.off()

        # Two's complement conversion for 24-bit signed integer
        if raw & 0x800000:
            raw -= 0x1000000

        dt.close()
        sck.close()
        return float(raw)

    except Exception as exc:
        logger.error("HX711 read failed: %s", exc)
        return _MOCK_RAW_VALUE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def tare() -> None:
    """
    Tare the scale: record the current raw reading as the zero baseline.

    Call with the empty dispensing cup in place before each dispense cycle.
    """
    global _tare_offset
    _tare_offset = _read_hx711_raw()
    logger.info("Scale tared (offset=%.0f)", _tare_offset)


def read_weight() -> float:
    """
    Return the current weight in grams (calibrated, tare-corrected).

    Returns:
        Weight in grams as a float.  Positive = weight above tare baseline.
    """
    raw = _read_hx711_raw()
    grams = (raw - _tare_offset) * CALIBRATION_FACTOR
    logger.debug("HX711 raw=%.0f tare=%.0f weight=%.2f g", raw, _tare_offset, grams)
    return grams


def wait_for_dispense_confirmation(
    timeout_seconds: float = 30.0,
    drop_threshold: float = DROP_THRESHOLD_G,
) -> bool:
    """
    Wait until the weight drops by at least drop_threshold grams (pill dispensed).

    Reads the weight at the moment of the call as the baseline, then polls
    until either:
      - The weight drops by >= drop_threshold → returns True (dispensed)
      - timeout_seconds elapses without that drop → returns False (no dispense)

    In mock mode (no hardware), returns True after a short delay.

    Args:
        timeout_seconds: Maximum time to wait in seconds.
        drop_threshold:  Minimum weight drop in grams to confirm dispense.

    Returns:
        True if dispense confirmed, False if timed out.
    """
    if not HARDWARE_AVAILABLE:
        # Mock: simulate pill falling after a brief pause
        time.sleep(0.05)
        logger.info("Mock sensor: dispense confirmed (mock mode)")
        return True

    baseline = read_weight()
    logger.info(
        "Waiting for dispense (baseline=%.1f g, threshold=%.1f g, timeout=%ss)",
        baseline,
        drop_threshold,
        timeout_seconds,
    )

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        current = read_weight()
        drop = baseline - current  # positive when weight decreases
        if drop >= drop_threshold:
            logger.info("Dispense confirmed (drop=%.1f g)", drop)
            return True
        time.sleep(POLL_INTERVAL_S)

    logger.warning(
        "Dispense not confirmed within %.1f s (threshold=%.1f g)",
        timeout_seconds,
        drop_threshold,
    )
    return False


# ---------------------------------------------------------------------------
# Backward-compatibility shims
# ---------------------------------------------------------------------------


def wait_for_extraction(
    timeout_seconds: int = 30,
    mock_delay: float = 0.1,
) -> bool:
    """
    Backward-compat shim — previously read an IR sensor.

    Now delegates to wait_for_dispense_confirmation() using the HX711.
    The mock_delay parameter is preserved for existing test compatibility
    but ignored in hardware mode (where the real poll loop controls timing).
    """
    if not HARDWARE_AVAILABLE:
        time.sleep(mock_delay)
        return True
    return wait_for_dispense_confirmation(timeout_seconds=float(timeout_seconds))


def read_button() -> bool:
    """
    Backward-compat stub — the physical button has been removed from the BOM.

    Always returns False.  Do not add new callers; this stub exists only to
    prevent import errors from legacy code paths.
    """
    logger.debug("read_button() called — no button hardware; returning False")
    return False
