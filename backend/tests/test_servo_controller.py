from __future__ import annotations

import pytest


def test_get_compartment_for_weekday_monday():
    from modules.servo_controller import get_compartment_for_weekday
    assert get_compartment_for_weekday(0) == 0


def test_get_compartment_for_weekday_sunday():
    from modules.servo_controller import get_compartment_for_weekday
    assert get_compartment_for_weekday(6) == 6


def test_move_to_compartment_mock_does_not_raise():
    from modules.servo_controller import move_to_compartment
    move_to_compartment(0)


def test_cleanup_does_not_raise():
    from modules.servo_controller import cleanup
    cleanup()
