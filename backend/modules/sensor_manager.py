from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    HARDWARE_AVAILABLE = False

EXTRACTION_PIN = 17
BUTTON_PIN = 27


def wait_for_extraction(timeout_seconds: int = 30, mock_delay: float = 0.1) -> bool:
    """Wait for pill extraction. Returns True when detected or in mock mode."""
    if HARDWARE_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(EXTRACTION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        start = time.time()
        while time.time() - start < timeout_seconds:
            if GPIO.input(EXTRACTION_PIN) == GPIO.LOW:
                return True
            time.sleep(0.05)
        return False
    else:
        time.sleep(mock_delay)
        return True


def read_button() -> bool:
    """Read the manual button state."""
    if HARDWARE_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        return GPIO.input(BUTTON_PIN) == GPIO.LOW
    else:
        return False
