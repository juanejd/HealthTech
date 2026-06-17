"""
Tests for the new HX711-based sensor manager (Fase 02 rewrite).

All tests run in mock mode (no real GPIO).
The weight-drop threshold logic is fully unit-testable via injected fakes.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# tare / read_weight
# ---------------------------------------------------------------------------

class TestTare:
    def test_tare_resets_offset(self):
        import modules.sensor_manager as sm
        sm._tare_offset = 99.0
        sm.tare()
        # In mock mode tare sets offset to a mock raw reading, not necessarily 0,
        # but read_weight() after tare() should return ~0.
        weight = sm.read_weight()
        assert abs(weight) < 1.0  # within 1 gram of zero after tare

    def test_tare_does_not_raise_in_mock_mode(self):
        import modules.sensor_manager as sm
        sm.tare()  # must not raise


class TestReadWeight:
    def test_returns_float(self):
        import modules.sensor_manager as sm
        result = sm.read_weight()
        assert isinstance(result, float)

    def test_after_tare_weight_is_near_zero(self):
        import modules.sensor_manager as sm
        sm.tare()
        weight = sm.read_weight()
        assert abs(weight) < 1.0


# ---------------------------------------------------------------------------
# wait_for_dispense_confirmation — threshold logic
# ---------------------------------------------------------------------------

class TestWaitForDispenseConfirmation:
    def test_returns_true_when_weight_drops_past_threshold(self):
        """
        Simulate: first reading 100 g (baseline), then 60 g (drop of 40 g).
        With drop_threshold=30, should return True.

        We patch HARDWARE_AVAILABLE=True so the real poll loop runs (not the
        mock-mode fast path), then supply fake read_weight values.
        """
        import modules.sensor_manager as sm

        readings = iter([100.0, 60.0])

        def fake_read():
            return next(readings)

        with patch.object(sm, "HARDWARE_AVAILABLE", True), \
             patch.object(sm, "read_weight", side_effect=fake_read):
            result = sm.wait_for_dispense_confirmation(
                timeout_seconds=5,
                drop_threshold=30.0,
            )

        assert result is True

    def test_returns_false_when_weight_does_not_drop(self):
        """Weight stays constant — should time out and return False."""
        import modules.sensor_manager as sm

        def fake_read():
            return 100.0  # never drops

        with patch.object(sm, "HARDWARE_AVAILABLE", True), \
             patch.object(sm, "read_weight", side_effect=fake_read):
            result = sm.wait_for_dispense_confirmation(
                timeout_seconds=0.1,  # short timeout for the test
                drop_threshold=30.0,
            )

        assert result is False

    def test_drop_exactly_at_threshold_returns_true(self):
        """A drop exactly equal to the threshold counts as dispensed."""
        import modules.sensor_manager as sm

        readings = iter([100.0, 70.0])  # drop = 30.0, threshold = 30.0

        def fake_read():
            return next(readings)

        with patch.object(sm, "HARDWARE_AVAILABLE", True), \
             patch.object(sm, "read_weight", side_effect=fake_read):
            result = sm.wait_for_dispense_confirmation(
                timeout_seconds=5,
                drop_threshold=30.0,
            )

        assert result is True

    def test_drop_below_threshold_returns_false(self):
        """Weight drops but not enough — should not confirm."""
        import modules.sensor_manager as sm

        readings = iter([100.0, 90.0])  # drop = 10 g, threshold = 30 g

        def fake_read():
            return next(readings)

        with patch.object(sm, "HARDWARE_AVAILABLE", True), \
             patch.object(sm, "read_weight", side_effect=fake_read):
            result = sm.wait_for_dispense_confirmation(
                timeout_seconds=0.05,
                drop_threshold=30.0,
            )

        assert result is False

    def test_mock_mode_returns_true_quickly(self):
        """In mock mode (no patching), confirmation comes back without real hardware."""
        import modules.sensor_manager as sm
        # Verify HARDWARE_AVAILABLE is False (dev PC)
        assert not sm.HARDWARE_AVAILABLE

        start = time.monotonic()
        result = sm.wait_for_dispense_confirmation(timeout_seconds=5, drop_threshold=30.0)
        elapsed = time.monotonic() - start

        assert result is True
        assert elapsed < 1.0  # should not block the full timeout


# ---------------------------------------------------------------------------
# Backward-compat shim: wait_for_extraction
# ---------------------------------------------------------------------------

class TestBackwardCompatShim:
    def test_wait_for_extraction_returns_true_in_mock(self):
        from modules.sensor_manager import wait_for_extraction
        result = wait_for_extraction(timeout_seconds=1, mock_delay=0.01)
        assert result is True

    def test_no_read_button_public_api(self):
        """read_button is removed — callers must not use it."""
        import modules.sensor_manager as sm
        # We keep the shim for backward compat during transition;
        # verify it still exists and returns False (no button hardware).
        assert hasattr(sm, "read_button")
        assert sm.read_button() is False
