from __future__ import annotations

import pytest


def test_wait_for_extraction_mock_returns_true():
    from modules.sensor_manager import wait_for_extraction
    result = wait_for_extraction(timeout_seconds=1, mock_delay=0.01)
    assert result is True


def test_read_button_mock_returns_false():
    from modules.sensor_manager import read_button
    result = read_button()
    assert result is False
