from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    import subprocess
    _result = subprocess.run(
        ["espeak-ng", "--version"],
        capture_output=True,
        timeout=2,
    )
    _ESPEAK_AVAILABLE = _result.returncode == 0
except Exception:
    _ESPEAK_AVAILABLE = False


def speak(message: str) -> None:
    """Speak a message via espeak-ng or log it in mock mode."""
    if _ESPEAK_AVAILABLE:
        try:
            import subprocess
            subprocess.run(["espeak-ng", message], check=False)
        except Exception as exc:
            logger.warning("TTS failed: %s", exc)
    else:
        logger.info("Mock TTS: %s", message)
