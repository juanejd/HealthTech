from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

try:
    import telegram
    _TELEGRAM_LIB_AVAILABLE = True
except ImportError:
    _TELEGRAM_LIB_AVAILABLE = False

_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def is_connected() -> bool:
    """Returns True only if token, chat_id, and the lib are all available."""
    return bool(_BOT_TOKEN and _CHAT_ID and _TELEGRAM_LIB_AVAILABLE)


def send_notification(event: dict) -> bool:
    """Send a notification. Returns False in mock/no-creds mode."""
    if not is_connected():
        logger.info("Mock Telegram notification: %s", event)
        return False
    try:
        import asyncio
        import telegram as tg

        async def _send() -> None:
            bot = tg.Bot(token=_BOT_TOKEN)
            msg = (
                f"Dispense event\n"
                f"Status: {event.get('status')}\n"
                f"Day: {event.get('day')}\n"
                f"Extracted: {event.get('extraction_detected')}"
            )
            await bot.send_message(chat_id=_CHAT_ID, text=msg)

        asyncio.run(_send())
        return True
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)
        return False
