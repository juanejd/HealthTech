from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_log_event_creates_file(tmp_path):
    log_file = tmp_path / "events.log"
    with patch("modules.logger.LOG_FILE", log_file):
        from modules.logger import log_event
        log_event("dispense", "OK", True, "lunes", 0)
    assert log_file.exists()


def test_log_event_writes_valid_json(tmp_path):
    log_file = tmp_path / "events.log"
    with patch("modules.logger.LOG_FILE", log_file):
        from modules.logger import log_event
        log_event("dispense", "OK", True, "lunes", 0)
    line = log_file.read_text().strip()
    event = json.loads(line)
    assert event["type"] == "dispense"
    assert event["status"] == "OK"
    assert event["extraction_detected"] is True
    assert event["day"] == "lunes"
    assert event["compartment_index"] == 0
    assert event["timestamp"].endswith("Z")


def test_log_event_appends(tmp_path):
    log_file = tmp_path / "events.log"
    with patch("modules.logger.LOG_FILE", log_file):
        from modules.logger import log_event
        log_event("dispense", "OK", True, "lunes", 0)
        log_event("dispense", "FAIL", False, "martes", 1)
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2


def test_read_events_returns_newest_first(tmp_path):
    log_file = tmp_path / "events.log"
    with patch("modules.logger.LOG_FILE", log_file):
        from modules.logger import log_event, read_events
        log_event("dispense", "OK", True, "lunes", 0)
        log_event("dispense", "FAIL", False, "martes", 1)
        events = read_events()
    assert events[0]["day"] == "martes"
    assert events[1]["day"] == "lunes"


def test_read_events_empty_file(tmp_path):
    log_file = tmp_path / "events.log"
    with patch("modules.logger.LOG_FILE", log_file):
        from modules.logger import read_events
        events = read_events()
    assert events == []
