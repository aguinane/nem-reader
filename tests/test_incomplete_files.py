import pytest

from nemreader import NEMFile


def test_correct_NMIs():

    nf = NEMFile("examples/invalid/Example_NEM12_powercor.csv", strict=False)
    meter_data = nf.nem_data()
    assert len(meter_data.readings) == 1
    assert "VABD000163" in meter_data.readings


def test_incomplete_interval_row():
    nf = NEMFile("examples/invalid/Example_NEM12_incomplete_interval.csv", strict=False)
    meter_data = nf.nem_data()
    assert len(meter_data.readings) == 1
    assert "VABD000163" in meter_data.readings


def test_correct_channels():
    nf = NEMFile("examples/invalid/Example_NEM12_powercor.csv", strict=False)
    meter_data = nf.nem_data()
    readings = meter_data.readings["VABD000163"]
    assert len(readings) == 2
    assert "E1" in readings
    assert "Q1" in readings


def test_correct_records():
    nf = NEMFile("examples/invalid/Example_NEM12_powercor.csv", strict=False)
    meter_data = nf.nem_data()
    readings = meter_data.readings["VABD000163"]

    assert len(readings["E1"]) == 96
    assert readings["E1"][10].read_value == pytest.approx(1.11, 0.1)
    assert readings["E1"][-1].read_value == pytest.approx(3.33, 0.1)

    assert len(readings["Q1"]) == 96
    assert readings["Q1"][10].read_value == pytest.approx(2.22, 0.1)
    assert readings["Q1"][-1].read_value == pytest.approx(4.44, 0.1)
    assert readings["Q1"][-1].quality_method == "A"


def test_zipped_load():
    nf = NEMFile("examples/invalid/Example_NEM12_powercor.csv.zip", strict=False)
    meter_data = nf.nem_data()
    assert "VABD000163" in meter_data.nmis


def test_missing_fields():
    nf = NEMFile("examples/invalid/Example_NEM12_powercor.csv", strict=False)
    meter_data = nf.nem_data()
    assert "VABD000163" in meter_data.nmis
