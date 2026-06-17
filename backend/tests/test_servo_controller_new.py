"""
Tests for the new FS90R servo controller (Fase 02 rewrite).

All tests run in mock mode (HARDWARE_AVAILABLE=False on any dev PC).
No real GPIO is touched — position state uses a tmp_path fixture.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module(position_file: Path):
    """
    Re-import servo_controller with the position file redirected to tmp_path.
    We patch the module-level constant after import so tests are isolated.
    """
    import importlib
    import modules.servo_controller as sc
    importlib.reload(sc)
    sc.POSITION_FILE = position_file
    # Reset in-memory position to match an empty / missing file
    sc._position = 0
    if position_file.exists():
        try:
            sc._position = json.loads(position_file.read_text())["position"]
        except Exception:
            sc._position = 0
    return sc


# ---------------------------------------------------------------------------
# get_position / set_home / reset_position
# ---------------------------------------------------------------------------

class TestGetPosition:
    def test_initial_position_is_zero(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        assert sc.get_position() == 0

    def test_position_file_missing_returns_zero(self, tmp_path):
        sc = _load_module(tmp_path / "nonexistent.json")
        assert sc.get_position() == 0

    def test_position_file_loaded_on_startup(self, tmp_path):
        pos_file = tmp_path / "pos.json"
        pos_file.write_text(json.dumps({"position": 5}))
        sc = _load_module(pos_file)
        assert sc.get_position() == 5


class TestSetHome:
    def test_set_home_resets_position_to_zero(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 4
        sc.set_home()
        assert sc.get_position() == 0

    def test_set_home_persists_zero_to_file(self, tmp_path):
        pos_file = tmp_path / "pos.json"
        sc = _load_module(pos_file)
        sc._position = 3
        sc.set_home()
        data = json.loads(pos_file.read_text())
        assert data["position"] == 0

    def test_reset_position_is_alias_for_set_home(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 6
        sc.reset_position()
        assert sc.get_position() == 0


# ---------------------------------------------------------------------------
# step_one_compartment
# ---------------------------------------------------------------------------

class TestStepOneCompartment:
    def test_advances_position_by_one(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 0
        sc.step_one_compartment()
        assert sc.get_position() == 1

    def test_position_wraps_at_eight(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 7
        sc.step_one_compartment()
        assert sc.get_position() == 0

    def test_persists_position_after_step(self, tmp_path):
        pos_file = tmp_path / "pos.json"
        sc = _load_module(pos_file)
        sc._position = 2
        sc.step_one_compartment()
        data = json.loads(pos_file.read_text())
        assert data["position"] == 3

    def test_step_does_not_raise_in_mock_mode(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc.step_one_compartment()  # must not raise


# ---------------------------------------------------------------------------
# advance_to_compartment
# ---------------------------------------------------------------------------

class TestAdvanceToCompartment:
    def test_advance_from_zero_to_three_takes_three_steps(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 0
        steps = []

        original_step = sc.step_one_compartment

        def counting_step():
            steps.append(1)
            original_step()

        with patch.object(sc, "step_one_compartment", side_effect=counting_step):
            sc.advance_to_compartment(3)

        assert len(steps) == 3
        assert sc.get_position() == 3

    def test_advance_wraps_correctly(self, tmp_path):
        """From position 6 to target 2 must take 4 steps (6→7→0→1→2)."""
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 6
        steps = []

        original_step = sc.step_one_compartment

        def counting_step():
            steps.append(1)
            original_step()

        with patch.object(sc, "step_one_compartment", side_effect=counting_step):
            sc.advance_to_compartment(2)

        assert len(steps) == 4
        assert sc.get_position() == 2

    def test_advance_to_current_position_is_zero_steps(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 3
        steps = []

        original_step = sc.step_one_compartment

        def counting_step():
            steps.append(1)
            original_step()

        with patch.object(sc, "step_one_compartment", side_effect=counting_step):
            sc.advance_to_compartment(3)

        assert len(steps) == 0

    def test_advance_to_invalid_index_raises(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        with pytest.raises(ValueError):
            sc.advance_to_compartment(8)

    def test_advance_to_negative_index_raises(self, tmp_path):
        sc = _load_module(tmp_path / "pos.json")
        with pytest.raises(ValueError):
            sc.advance_to_compartment(-1)

    def test_full_rotation_eight_steps(self, tmp_path):
        """
        From position 0 to 0 after a full rotation: only makes sense if we
        explicitly want 8 steps — but advance_to_compartment(current) == 0 steps.
        Going to position 0 from position 1 should be 7 steps (forward only).
        """
        sc = _load_module(tmp_path / "pos.json")
        sc._position = 1
        steps = []

        original_step = sc.step_one_compartment

        def counting_step():
            steps.append(1)
            original_step()

        with patch.object(sc, "step_one_compartment", side_effect=counting_step):
            sc.advance_to_compartment(0)

        assert len(steps) == 7
        assert sc.get_position() == 0


# ---------------------------------------------------------------------------
# Backward-compat shim
# ---------------------------------------------------------------------------

class TestBackwardCompatShim:
    def test_get_compartment_for_weekday_monday(self):
        from modules.servo_controller import get_compartment_for_weekday
        assert get_compartment_for_weekday(0) == 0

    def test_get_compartment_for_weekday_sunday(self):
        from modules.servo_controller import get_compartment_for_weekday
        assert get_compartment_for_weekday(6) == 6

    def test_move_to_compartment_does_not_raise(self, tmp_path):
        import modules.servo_controller as sc
        sc.POSITION_FILE = tmp_path / "pos.json"
        sc._position = 0
        from modules.servo_controller import move_to_compartment
        move_to_compartment(0)

    def test_cleanup_does_not_raise(self):
        from modules.servo_controller import cleanup
        cleanup()
