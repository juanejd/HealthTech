"""
Tests for HX711 calibration persistence (factor load/save/apply).

The calibration factor converts raw 24-bit ADC counts into grams.  It must be
persisted to disk so it survives restarts, loaded at module init, and applied
by read_weight().  All tests run in mock mode (no real GPIO).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Restore mutable module globals after each test to avoid cross-test leak."""
    import modules.sensor_manager as sm
    saved_factor = sm.CALIBRATION_FACTOR
    saved_offset = sm._tare_offset
    yield
    sm.CALIBRATION_FACTOR = saved_factor
    sm._tare_offset = saved_offset


class TestReadWeightRaw:
    def test_returns_tare_corrected_delta_without_factor(self):
        """read_weight_raw() returns (raw - tare), NOT multiplied by the factor.

        This is the value the calibration routine divides a known weight by.
        """
        import modules.sensor_manager as sm
        seq = iter([500000.0, 600000.0])
        with patch.object(sm, "_read_hx711_raw", side_effect=lambda: next(seq)):
            sm.tare()                      # offset = 500000
            delta = sm.read_weight_raw()   # 600000 - 500000
        assert delta == 100000.0


class TestCalibrationPersistence:
    def test_save_then_load_round_trip(self, tmp_path, monkeypatch):
        import modules.sensor_manager as sm
        monkeypatch.setattr(sm, "CALIBRATION_FILE", tmp_path / "cal.json")
        sm.save_calibration(0.0005)
        assert sm.load_calibration() == 0.0005

    def test_load_returns_default_when_file_missing(self, tmp_path, monkeypatch):
        import modules.sensor_manager as sm
        monkeypatch.setattr(sm, "CALIBRATION_FILE", tmp_path / "missing.json")
        assert sm.load_calibration() == 1.0

    def test_load_returns_default_when_file_corrupt(self, tmp_path, monkeypatch):
        import modules.sensor_manager as sm
        bad = tmp_path / "cal.json"
        bad.write_text("not json", encoding="utf-8")
        monkeypatch.setattr(sm, "CALIBRATION_FILE", bad)
        assert sm.load_calibration() == 1.0


class TestSetCalibrationFactor:
    def test_persists_to_disk(self, tmp_path, monkeypatch):
        import modules.sensor_manager as sm
        monkeypatch.setattr(sm, "CALIBRATION_FILE", tmp_path / "cal.json")
        sm.set_calibration_factor(0.0005)
        assert sm.load_calibration() == 0.0005

    def test_makes_read_weight_return_grams(self, tmp_path, monkeypatch):
        """After calibrating, read_weight() converts raw counts to grams."""
        import modules.sensor_manager as sm
        monkeypatch.setattr(sm, "CALIBRATION_FILE", tmp_path / "cal.json")
        seq = iter([500000.0, 600000.0])
        with patch.object(sm, "_read_hx711_raw", side_effect=lambda: next(seq)):
            sm.tare()                                  # offset = 500000
            sm.set_calibration_factor(50.0 / 100000.0)  # 100000 counts = 50 g
            grams = sm.read_weight()                    # (600000-500000) * factor
        assert abs(grams - 50.0) < 1e-6
