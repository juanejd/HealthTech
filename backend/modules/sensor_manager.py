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
  sudo apt install -y python3-lgpio   # default GPIO backend on Bookworm

Calibration:
  1. Call tare() with the empty dispensing cup on the scale.
  2. Place a known reference weight and read read_weight().
  3. Set CALIBRATION_FACTOR = known_weight_grams / raw_delta
     (use scripts/hx711_calibrate.py, which persists the factor).
  4. Adjust DROP_THRESHOLD_G to match the lightest pill in your formulary.

The HX711 is bit-banged directly via lgpio (gpio_read/gpio_write).  An earlier
gpiozero DigitalInputDevice/DigitalOutputDevice implementation was too slow —
PD_SCK stayed HIGH >60µs and the chip powered down mid-read, returning garbage.
If lgpio is not available (dev PC), the module operates in mock mode.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hardware import guard
# ---------------------------------------------------------------------------

try:
    import lgpio

    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    lgpio = None
    HARDWARE_AVAILABLE = False


class HX711Error(RuntimeError):
    """Raised when the HX711 fails to deliver data (e.g. DRDY timeout).

    Surfacing this is deliberate: returning a fake value on failure would mask
    a dead sensor and let a dispense be falsely confirmed.
    """


# ---------------------------------------------------------------------------
# Pin assignments (BCM)
# ---------------------------------------------------------------------------

HX711_DT_PIN: int = 17  # data  (DOUT)
HX711_SCK_PIN: int = 23  # clock (PD_SCK)

# gpiochip device index (0 on Raspberry Pi).
GPIO_CHIP: int = 0

# How long to wait for the HX711 to signal "data ready" (DOUT goes LOW).
DRDY_TIMEOUT_S: float = 1.0

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

# Default factor used when no calibration file exists yet (raw counts ≈ grams).
DEFAULT_CALIBRATION_FACTOR: float = 1.0

# Persisted calibration factor, written by scripts/hx711_calibrate.py and
# reloaded at module init so the value survives restarts.
CALIBRATION_FILE: Path = (
    Path(__file__).parent.parent / "logs" / "hx711_calibration.json"
)

# ---------------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------------

_tare_offset: float = 0.0

# ---------------------------------------------------------------------------
# Internal HX711 bit-bang read
# ---------------------------------------------------------------------------

_MOCK_RAW_VALUE: float = 500000.0  # stable mock raw reading

# Lazily-opened lgpio chip handle, reused across reads. Released by cleanup().
_chip_handle = None


def _to_signed_24(raw: int) -> int:
    """Convert a 24-bit unsigned value to a signed integer (two's complement)."""
    if raw & 0x800000:
        return raw - 0x1000000
    return raw


def _ensure_handle() -> int:
    """Open the gpiochip and claim DT (input) / SCK (output, LOW) once."""
    global _chip_handle
    if _chip_handle is None:
        _chip_handle = lgpio.gpiochip_open(GPIO_CHIP)
        lgpio.gpio_claim_input(_chip_handle, HX711_DT_PIN)
        lgpio.gpio_claim_output(_chip_handle, HX711_SCK_PIN, 0)  # SCK starts LOW
    return _chip_handle


def _read_hx711_raw() -> float:
    """
    Read one 24-bit value from the HX711 via a direct lgpio bit-bang.

    gpiozero's DigitalInputDevice/DigitalOutputDevice were too slow: each call
    took ~100µs, so PD_SCK stayed HIGH >60µs and the HX711 powered down mid-read,
    returning garbage (~0). lgpio's gpio_read/gpio_write are fast enough.

    Returns the signed 24-bit reading as a float. In mock mode (dev PC, no lgpio)
    returns a stable constant. On a real DRDY timeout raises HX711Error rather
    than masking the fault with a fake value.
    """
    if not HARDWARE_AVAILABLE:
        return _MOCK_RAW_VALUE

    handle = _ensure_handle()

    # Wait for DRDY: the HX711 holds DOUT HIGH until a conversion is ready.
    deadline = time.monotonic() + DRDY_TIMEOUT_S
    while lgpio.gpio_read(handle, HX711_DT_PIN) == 1:
        if time.monotonic() > deadline:
            raise HX711Error("DRDY timeout — HX711 not responding")
        time.sleep(0.001)

    # Clock in 24 bits, MSB first.
    raw = 0
    for _ in range(24):
        lgpio.gpio_write(handle, HX711_SCK_PIN, 1)
        bit = lgpio.gpio_read(handle, HX711_DT_PIN)
        lgpio.gpio_write(handle, HX711_SCK_PIN, 0)
        raw = (raw << 1) | bit

    # 25th pulse selects channel A, gain 128 for the next conversion.
    lgpio.gpio_write(handle, HX711_SCK_PIN, 1)
    lgpio.gpio_write(handle, HX711_SCK_PIN, 0)

    return float(_to_signed_24(raw))


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


def read_weight_raw() -> float:
    """
    Return the tare-corrected raw ADC delta (counts), WITHOUT the calibration factor.

    This is the value the calibration routine divides a known reference weight by
    to compute CALIBRATION_FACTOR. Use read_weight() for grams in normal operation.
    """
    return _read_hx711_raw() - _tare_offset


def load_calibration() -> float:
    """
    Load the persisted calibration factor from CALIBRATION_FILE.

    Returns DEFAULT_CALIBRATION_FACTOR if the file is missing or unreadable.
    """
    try:
        data = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        return float(data["calibration_factor"])
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return DEFAULT_CALIBRATION_FACTOR


def save_calibration(factor: float) -> None:
    """Persist the calibration factor to CALIBRATION_FILE."""
    try:
        CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIBRATION_FILE.write_text(
            json.dumps({"calibration_factor": factor}), encoding="utf-8"
        )
    except OSError as exc:
        logger.error("Failed to persist calibration factor: %s", exc)


def set_calibration_factor(factor: float) -> None:
    """
    Update the active calibration factor and persist it to disk.

    Subsequent read_weight() calls use the new factor immediately.
    """
    global CALIBRATION_FACTOR
    CALIBRATION_FACTOR = factor
    save_calibration(factor)
    logger.info("Calibration factor set to %.8g", factor)


def cleanup() -> None:
    """Release the lgpio chip handle. Call on application shutdown."""
    global _chip_handle
    if _chip_handle is not None and lgpio is not None:
        try:
            lgpio.gpiochip_close(_chip_handle)
        except Exception as exc:
            logger.debug("HX711 cleanup: %s", exc)
        finally:
            _chip_handle = None


# Load any persisted calibration at import time (defaults to 1.0 if absent).
CALIBRATION_FACTOR = load_calibration()


def wait_for_dispense_confirmation(
    timeout_seconds: float = 30.0,
    drop_threshold: float = DROP_THRESHOLD_G,
) -> bool:
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


def wait_for_extraction(
    timeout_seconds: int = 30,
    mock_delay: float = 0.1,
) -> bool:

    if not HARDWARE_AVAILABLE:
        time.sleep(mock_delay)
        return True
    return wait_for_dispense_confirmation(timeout_seconds=float(timeout_seconds))


def read_button() -> bool:

    logger.debug("read_button() called — no button hardware; returning False")
    return False
