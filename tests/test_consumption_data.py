import pytest

from nemreader import NEMFile


def test_nem13_readings():
    """Test the NEM13 consumption data"""
    nf = NEMFile("examples/unzipped/Example_NEM13_consumption_data.csv", strict=True)
    meter_data = nf.nem_data()
    readings = meter_data.readings["VABC005890"]["11"]
    unit_count = 0
    for record in readings:
        unit_count += record[2]  # Read value should be third record in tuple
        assert unit_count == pytest.approx(1312.1, 0.1)
