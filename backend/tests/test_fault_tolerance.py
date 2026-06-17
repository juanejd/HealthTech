from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


def test_enqueue_adds_notification(tmp_path):
    queue_file = tmp_path / "pending_notifications.json"
    with patch("modules.fault_tolerance.QUEUE_FILE", queue_file):
        from modules.fault_tolerance import enqueue, get_pending_count
        enqueue({"event": "dispense", "status": "OK"})
        assert get_pending_count() == 1


def test_dequeue_all_returns_and_clears(tmp_path):
    queue_file = tmp_path / "pending_notifications.json"
    with patch("modules.fault_tolerance.QUEUE_FILE", queue_file):
        from modules.fault_tolerance import enqueue, dequeue_all, get_pending_count
        enqueue({"event": "dispense"})
        enqueue({"event": "alert"})
        result = dequeue_all()
        assert len(result) == 2
        assert get_pending_count() == 0


def test_max_queue_size_drops_oldest(tmp_path):
    queue_file = tmp_path / "pending_notifications.json"
    with patch("modules.fault_tolerance.QUEUE_FILE", queue_file):
        from modules.fault_tolerance import enqueue, get_pending_count
        for i in range(105):
            enqueue({"index": i})
        assert get_pending_count() == 100


def test_dequeue_all_empty(tmp_path):
    queue_file = tmp_path / "pending_notifications.json"
    with patch("modules.fault_tolerance.QUEUE_FILE", queue_file):
        from modules.fault_tolerance import dequeue_all
        result = dequeue_all()
        assert result == []
