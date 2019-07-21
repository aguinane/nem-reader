""" Test Suite
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import nemreader as nr


def test_correct_NMIs():
    meter_data = nr.read_nem_file("examples/unzipped/Example_NEM12_actual_interval.csv")
    assert len(meter_data.readings) == 1
    assert "VABD000163" in meter_data.readings


def test_correct_channels():
    meter_data = nr.read_nem_file("examples/unzipped/Example_NEM12_actual_interval.csv")
    readings = meter_data.readings["VABD000163"]
    assert len(readings) == 2
    assert "E1" in readings
    assert "Q1" in readings


def test_correct_records():
    meter_data = nr.read_nem_file("examples/unzipped/Example_NEM12_actual_interval.csv")
    readings = meter_data.readings["VABD000163"]

    assert len(readings["E1"]) == 48
    assert readings["E1"][10].read_value == pytest.approx(1.11, 0.1)
    assert readings["E1"][-1].read_value == pytest.approx(1.11, 0.1)

    assert len(readings["Q1"]) == 48
    assert readings["Q1"][10].read_value == pytest.approx(2.22, 0.1)
    assert readings["Q1"][-1].read_value == pytest.approx(2.22, 0.1)
    assert readings["Q1"][-1].quality_method == "A"
