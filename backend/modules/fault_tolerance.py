from __future__ import annotations

import json
from pathlib import Path
from typing import List

QUEUE_FILE: Path = Path(__file__).parent.parent / "logs" / "pending_notifications.json"
MAX_QUEUE_SIZE = 100


def _load_queue() -> List[dict]:
    """Load queue from disk. Always reads the current QUEUE_FILE value."""
    queue_path = QUEUE_FILE
    if queue_path.exists():
        try:
            data = json.loads(queue_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, Exception):
            return []
    return []


def _persist_queue(queue: List[dict]) -> None:
    """Persist queue to disk. Always uses the current QUEUE_FILE value."""
    queue_path = QUEUE_FILE
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(queue), encoding="utf-8")


def enqueue(notification: dict) -> None:
    queue = _load_queue()
    queue.append(notification)
    if len(queue) > MAX_QUEUE_SIZE:
        queue = queue[-MAX_QUEUE_SIZE:]
    _persist_queue(queue)


def dequeue_all() -> List[dict]:
    queue = _load_queue()
    _persist_queue([])
    return queue


def get_pending_count() -> int:
    return len(_load_queue())
