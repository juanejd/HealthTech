"""
servo_controller.py — FS90R continuous-rotation servo driver.

Hardware: FS90R connected to GPIO18 (BCM), driven via gpiozero (lgpio backend).

The carousel has 8 positions (0–7):
  - Position 0: home / drop slot (refilled weekly by caregiver)
  - Positions 1–7: day compartments (Mon–Sun)

Positioning is OPEN-LOOP: the servo runs at a fixed speed for a calibrated
duration (STEP_DURATION_S) to advance one 45° step.  The current position is
persisted in POSITION_FILE so it survives restarts.

Pi setup (run once on the Pi):
  sudo apt install -y python3-lgpio   # default GPIO backend on Bookworm
  pip install gpiozero

Calibration (on real hardware):
  1. Run hw_selftest.py to verify raw servo response.
  2. Adjust STEP_DURATION_S until one call to step_one_compartment() rotates
     the carousel exactly 45°.
  3. If the servo drifts at neutral, fine-tune STOP_VALUE so the carousel
     stops completely when value=STOP_VALUE.
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
    from gpiozero import Servo

    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    HARDWARE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Pin assignment
# ---------------------------------------------------------------------------

SERVO_GPIO_PIN: int = 18  # BCM

# ---------------------------------------------------------------------------
# Calibration constants — tune on real hardware
# ---------------------------------------------------------------------------

# Neutral (stop) pulse for the FS90R.  The FS90R spec says 1.5 ms = stop, but
# manufactured tolerances vary.  0.0 maps to 1.5 ms in gpiozero's Servo class.
STOP_VALUE: float = 0.0

# Direction: +1.0 = forward (CCW when viewed from top); flip to -1.0 if the
# carousel rotates the wrong way.
DIRECTION: float = 1.0

# Speed fraction applied to DIRECTION.  1.0 = full speed.
STEP_SPEED: float = 1.0

# How long to run the servo per 45° step.  Adjust until one step ≈ 45°.
STEP_DURATION_S: float = 0.25

# Total number of carousel positions (7 day compartments + 1 home/drop slot).
NUM_POSITIONS: int = 8

# ---------------------------------------------------------------------------
# Position persistence
# ---------------------------------------------------------------------------

POSITION_FILE: Path = Path(__file__).parent.parent / "logs" / "carousel_position.json"

_position: int = 0


def _load_position() -> int:
    try:
        data = json.loads(POSITION_FILE.read_text(encoding="utf-8"))
        return int(data.get("position", 0)) % NUM_POSITIONS
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return 0


def _save_position(index: int) -> None:
    try:
        POSITION_FILE.parent.mkdir(parents=True, exist_ok=True)
        POSITION_FILE.write_text(json.dumps({"position": index}), encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to persist carousel position: %s", exc)


def _get_servo() -> "Servo | None":
    if not HARDWARE_AVAILABLE:
        return None
    try:
        return Servo(SERVO_GPIO_PIN)
    except Exception as exc:
        logger.error("Failed to initialize servo on GPIO%d: %s", SERVO_GPIO_PIN, exc)
        return None


# ---------------------------------------------------------------------------
# Module initialisation — load persisted position
# ---------------------------------------------------------------------------

_position = _load_position()


def get_position() -> int:
    return _position


def set_home() -> None:
    global _position
    _position = 0
    _save_position(0)
    logger.info("Carousel homed to position 0")


def reset_position() -> None:
    set_home()


def stop() -> None:
    """
    Stop the servo immediately.

    In hardware mode, momentarily attaches a Servo instance set to STOP_VALUE
    then detaches it.  In mock mode, logs only.
    """
    if HARDWARE_AVAILABLE:
        servo = _get_servo()
        if servo is not None:
            try:
                servo.value = STOP_VALUE
                time.sleep(0.05)
                servo.detach()
            except Exception as exc:
                logger.error("Failed to stop servo: %s", exc)
            finally:
                servo.close()
    else:
        logger.debug("Mock servo: stop called")


def step_one_compartment() -> None:
    global _position

    if HARDWARE_AVAILABLE:
        servo = _get_servo()
        if servo is not None:
            try:
                servo.value = STEP_SPEED * DIRECTION
                time.sleep(STEP_DURATION_S)
                servo.value = STOP_VALUE
                time.sleep(0.05)  # brief settle
            except Exception as exc:
                logger.error("Servo step failed: %s", exc)
            finally:
                servo.detach()
                servo.close()
        else:
            logger.warning("Servo unavailable — position incremented without movement")
    else:
        logger.info("Mock servo: stepping (STEP_DURATION_S=%.3fs)", STEP_DURATION_S)
        time.sleep(0.001)  # negligible delay in tests

    _position = (_position + 1) % NUM_POSITIONS
    _save_position(_position)
    logger.debug("Carousel position → %d", _position)


def advance_to_compartment(target_index: int) -> None:
    """
    Advance the carousel forward (only) to target_index.

    Calculates the minimum number of forward 45° steps needed from the current
    position and executes them sequentially.  The carousel only moves in one
    direction; if target_index == current position, no steps are taken.

    Args:
        target_index: Destination compartment index in range [0, NUM_POSITIONS).

    Raises:
        ValueError: If target_index is outside [0, NUM_POSITIONS).
    """
    if not (0 <= target_index < NUM_POSITIONS):
        raise ValueError(
            f"target_index must be in [0, {NUM_POSITIONS - 1}], got {target_index}"
        )

    steps_needed = (target_index - _position) % NUM_POSITIONS
    logger.info(
        "Advancing carousel: %d → %d (%d steps)",
        _position,
        target_index,
        steps_needed,
    )
    for _ in range(steps_needed):
        step_one_compartment()


def cleanup() -> None:
    """Release GPIO resources.  Call on application shutdown."""
    if HARDWARE_AVAILABLE:
        try:
            from gpiozero import Device

            Device.close()
        except Exception as exc:
            logger.debug("GPIO cleanup: %s", exc)
    else:
        logger.debug("Mock servo: cleanup called")


def get_compartment_for_weekday(weekday: int) -> int:
    """Map a Python weekday (0=Monday … 6=Sunday) to a carousel compartment index.

    Compartment 0 is reserved for the home/drop slot; day compartments occupy
    positions 1–7 (Monday=1, …, Sunday=7).

    Args:
        weekday: Value returned by datetime.weekday() — must be in [0, 6].

    Returns:
        Carousel compartment index in [1, 7].

    Raises:
        ValueError: If weekday is outside the valid range [0, 6].
    """
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday must be in [0, 6], got {weekday}")
    return weekday + 1


def move_to_compartment(day_index: int) -> None:
    advance_to_compartment(day_index)
