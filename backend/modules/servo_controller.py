from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    HARDWARE_AVAILABLE = False


def get_compartment_for_weekday(weekday: int) -> int:
    """Maps Monday=0..Sunday=6 to compartment 0..6."""
    return weekday


def move_to_compartment(day_index: int) -> None:
    """Move servo to compartment for the given day index."""
    if HARDWARE_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)
        pwm = GPIO.PWM(18, 50)
        pwm.start(0)
        duty = 2.5 + (day_index / 6.0) * 10
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        pwm.stop()
    else:
        logger.info("Mock servo: moving to compartment %d", day_index)
        time.sleep(0.05)


def cleanup() -> None:
    """Release GPIO resources."""
    if HARDWARE_AVAILABLE:
        GPIO.cleanup()
    else:
        logger.debug("Mock servo: cleanup called")
