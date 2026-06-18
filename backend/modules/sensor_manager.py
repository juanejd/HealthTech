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
import os
import statistics
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

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


HX711_READ_RETRIES: int = 2


FILTER_SAMPLES: int = 5
POLL_FILTER_SAMPLES: int = 3

# MAD (Median Absolute Deviation) outlier gate — threshold in units of MAD.
FILTER_MAD_THRESHOLD: float = 3.0

# Set to True to enable MAD outlier rejection inside _read_filtered().
FILTER_MAD_ENABLED: bool = False


_tare_offset: float = 0.0

_calibration_loaded_from_file: bool = False


_MOCK_RAW_VALUE: float = 500000.0
_MOCK_DISPENSE_CONFIRMED: bool = os.environ.get(
    "HEALTHTECH_MOCK_DISPENSE", "1"
).strip().lower() not in ("0", "false", "no")

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
    """Read one 24-bit sample from the HX711 via direct lgpio bit-bang.

    This is the single-sample primitive. Higher-level callers use
    _read_filtered() which aggregates multiple samples via median.

    On a transient DRDY timeout the read is retried up to HX711_READ_RETRIES
    times (2), for a total of 3 attempts. Each retry is logged at WARNING level.
    If the budget is exhausted the final failure is logged at ERROR and
    HX711Error is raised — never returns a fake value on hardware failure.

    In mock mode (no lgpio) returns _MOCK_RAW_VALUE immediately.
    """
    if not HARDWARE_AVAILABLE:
        return _MOCK_RAW_VALUE

    handle = _ensure_handle()

    for attempt in range(1 + HX711_READ_RETRIES):
        # Wait for DRDY: HX711 holds DOUT HIGH until conversion is ready.
        deadline = time.monotonic() + DRDY_TIMEOUT_S
        while lgpio.gpio_read(handle, HX711_DT_PIN) == 1:
            if time.monotonic() > deadline:
                if attempt < HX711_READ_RETRIES:
                    logger.warning(
                        "HX711 DRDY timeout on attempt %d/%d — retrying",
                        attempt + 1,
                        1 + HX711_READ_RETRIES,
                    )
                    break  # retry the outer loop
                else:
                    logger.error(
                        "HX711 DRDY timeout — all %d attempts exhausted",
                        1 + HX711_READ_RETRIES,
                    )
                    raise HX711Error(
                        f"DRDY timeout after {1 + HX711_READ_RETRIES} attempts"
                    )
            time.sleep(0.001)
        else:
            # DRDY went LOW — proceed with clock-in.
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

    # Should not be reached, but satisfies type checkers.
    raise HX711Error("_read_hx711_raw: exhausted retry budget")


# ---------------------------------------------------------------------------
# Filtered read (D5)
# ---------------------------------------------------------------------------


def _read_filtered(samples: int = FILTER_SAMPLES) -> float:
    """Return a median-filtered raw reading from the HX711.

    Collects `samples` single-sample reads via _read_hx711_raw() and returns
    their median. When FILTER_MAD_ENABLED is True, samples that deviate from
    the median by more than FILTER_MAD_THRESHOLD * MAD are discarded before
    computing the final median (optional MAD outlier rejection).

    Args:
        samples: Number of raw samples to collect. Use FILTER_SAMPLES (5) for
                 one-shot operations (tare, baseline); POLL_FILTER_SAMPLES (3)
                 for the time-sensitive dispense poll loop.

    Returns:
        Median of the (filtered) sample set as a float.

    Raises:
        HX711Error: If any underlying _read_hx711_raw() call fails after retries.
    """
    readings = [_read_hx711_raw() for _ in range(samples)]

    if FILTER_MAD_ENABLED and len(readings) >= 3:
        med = statistics.median(readings)
        # Median Absolute Deviation
        mad = statistics.median([abs(x - med) for x in readings])
        if mad > 0:
            readings = [
                x for x in readings if abs(x - med) <= FILTER_MAD_THRESHOLD * mad
            ]
        # Fallback: if all samples are identical (mad == 0), keep all.

    return statistics.median(readings)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def tare() -> None:
    """
    Tare the scale: record the median-filtered raw reading as the zero baseline.

    Call with the empty dispensing cup in place before each dispense cycle.
    Uses FILTER_SAMPLES (5) reads for a robust baseline.
    """
    global _tare_offset
    _tare_offset = _read_filtered(FILTER_SAMPLES)
    logger.info("Scale tared (offset=%.0f)", _tare_offset)


def read_weight() -> float:
    """
    Return the current weight in grams (calibrated, tare-corrected).

    Uses _read_filtered() for noise reduction. Call FILTER_SAMPLES via tare first.

    Returns:
        Weight in grams as a float.  Positive = weight above tare baseline.
    """
    raw = _read_filtered(FILTER_SAMPLES)
    grams = (raw - _tare_offset) * CALIBRATION_FACTOR
    logger.debug("HX711 raw=%.0f tare=%.0f weight=%.2f g", raw, _tare_offset, grams)
    return grams


def read_weight_raw() -> float:
    """
    Return the tare-corrected raw ADC delta (counts), WITHOUT the calibration factor.

    Uses FILTER_SAMPLES reads for a cleaner calibration reference. Use read_weight()
    for gram values in normal operation.
    """
    return _read_filtered(FILTER_SAMPLES) - _tare_offset


def load_calibration() -> float:

    global _calibration_loaded_from_file
    try:
        data = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        factor = float(data["calibration_factor"])
        _calibration_loaded_from_file = True
        return factor
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        _calibration_loaded_from_file = False
        return DEFAULT_CALIBRATION_FACTOR


def is_calibrated() -> bool:
    return _calibration_loaded_from_file


def save_calibration(factor: float) -> None:
    try:
        CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIBRATION_FILE.write_text(
            json.dumps({"calibration_factor": factor}), encoding="utf-8"
        )
    except OSError as exc:
        logger.error("Failed to persist calibration factor: %s", exc)


def set_calibration_factor(factor: float) -> None:

    global CALIBRATION_FACTOR
    CALIBRATION_FACTOR = factor
    save_calibration(factor)
    logger.info("Calibration factor set to %.8g", factor)


def cleanup() -> None:
    global _chip_handle
    if _chip_handle is not None and lgpio is not None:
        try:
            lgpio.gpiochip_close(_chip_handle)
        except Exception as exc:
            logger.debug("HX711 cleanup: %s", exc)
        finally:
            _chip_handle = None


CALIBRATION_FACTOR = load_calibration()
if not _calibration_loaded_from_file:
    logger.warning(
        "HX711 not calibrated — weight readings are in raw ADC counts. "
        "Run scripts/hx711_calibrate.py on real hardware to generate %s.",
        CALIBRATION_FILE,
    )


def set_mock_dispense_confirmed(value: bool) -> None:
    global _MOCK_DISPENSE_CONFIRMED
    _MOCK_DISPENSE_CONFIRMED = value


def wait_for_dispense_confirmation(
    timeout_seconds: float = 30.0,
    drop_threshold: float = DROP_THRESHOLD_G,
) -> bool:
    if not HARDWARE_AVAILABLE:
        time.sleep(0.05)
        outcome = _MOCK_DISPENSE_CONFIRMED
        logger.info(
            "Mock sensor: dispense %s (mock mode)",
            "confirmed" if outcome else "not confirmed",
        )
        return outcome
    if not _calibration_loaded_from_file:
        logger.warning(
            "Dispense baseline read while uncalibrated — weight values are raw ADC counts"
        )
    baseline_raw = _read_filtered(FILTER_SAMPLES)
    baseline = (baseline_raw - _tare_offset) * CALIBRATION_FACTOR
    logger.info(
        "Waiting for dispense (baseline=%.1f raw, threshold=%.1f g, timeout=%ss)",
        baseline_raw,
        drop_threshold,
        timeout_seconds,
    )

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        current_raw = _read_filtered(POLL_FILTER_SAMPLES)
        current = (current_raw - _tare_offset) * CALIBRATION_FACTOR
        drop = baseline - current  # positive when weight decreases
        if drop >= drop_threshold:
            logger.info("Dispense confirmed (drop=%.1f)", drop)
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
