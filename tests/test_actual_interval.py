import pytest

from nemreader import NEMFile


def test_correct_NMIs():
    nf = NEMFile("examples/unzipped/Example_NEM12_actual_interval.csv", strict=True)
    meter_data = nf.nem_data()
    assert len(meter_data.readings) == 1
    assert "VABD000163" in meter_data.readings


def test_correct_channels():
    nf = NEMFile("examples/unzipped/Example_NEM12_actual_interval.csv", strict=True)
    meter_data = nf.nem_data()
    readings = meter_data.readings["VABD000163"]
    assert len(readings) == 2
    assert "E1" in readings
    assert "Q1" in readings


def test_correct_records():
    nf = NEMFile("examples/unzipped/Example_NEM12_actual_interval.csv", strict=True)
    meter_data = nf.nem_data()
    readings = meter_data.readings["VABD000163"]

    assert len(readings["E1"]) == 48
    assert readings["E1"][10].read_value == pytest.approx(1.11, 0.1)
    assert readings["E1"][-1].read_value == pytest.approx(1.11, 0.1)

    assert len(readings["Q1"]) == 48
    assert readings["Q1"][10].read_value == pytest.approx(2.22, 0.1)
    assert readings["Q1"][-1].read_value == pytest.approx(2.22, 0.1)
    assert readings["Q1"][-1].quality_method == "A"
