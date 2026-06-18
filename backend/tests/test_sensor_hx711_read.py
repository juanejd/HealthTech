"""
Tests for the lgpio-based HX711 raw read.

Root cause (confirmed on hardware): the gpiozero DigitalInputDevice/Output bit-bang
returns garbage (~0) because its per-bit calls are too slow and the HX711 powers
down mid-read. A direct lgpio bit-bang reads correctly. These tests pin down:
  - 24-bit two's-complement conversion (pure logic)
  - mock-mode behavior is preserved (dev PC)
  - bit assembly is MSB-first
  - a DRDY timeout on real hardware SURFACES a fault instead of returning a fake value
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import modules.sensor_manager as sm


class TestTwosComplement:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (0x000000, 0),
            (0x000001, 1),
            (0x7FFFFF, 8388607),
            (0x800000, -8388608),
            (0xFFFFFF, -1),
        ],
    )
    def test_to_signed_24(self, raw, expected):
        assert sm._to_signed_24(raw) == expected


class TestReadRawMockMode:
    def test_returns_mock_value_when_no_hardware(self):
        assert not sm.HARDWARE_AVAILABLE
        assert sm._read_hx711_raw() == sm._MOCK_RAW_VALUE


class TestReadRawHardware:
    def test_assembles_24_bits_msb_first(self):
        # DRDY ready immediately (0), then 24 bit reads encoding 0x00000F = 15.
        bits = [0] * 20 + [1, 1, 1, 1]   # MSB-first
        reads = iter([0] + bits)         # first read = DRDY poll
        fake = MagicMock()
        fake.gpio_read.side_effect = lambda h, p: next(reads)
        with patch.object(sm, "HARDWARE_AVAILABLE", True), \
             patch.object(sm, "lgpio", fake), \
             patch.object(sm, "_ensure_handle", return_value=1):
            value = sm._read_hx711_raw()
        assert value == 15.0

    def test_drdy_timeout_raises_instead_of_masking(self):
        fake = MagicMock()
        fake.gpio_read.return_value = 1   # DT never goes ready
        with patch.object(sm, "HARDWARE_AVAILABLE", True), \
             patch.object(sm, "lgpio", fake), \
             patch.object(sm, "_ensure_handle", return_value=1), \
             patch.object(sm, "DRDY_TIMEOUT_S", 0.01):
            with pytest.raises(sm.HX711Error):
                sm._read_hx711_raw()
