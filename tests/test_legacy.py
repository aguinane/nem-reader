from nemreader import read_nem_file


def test_correct_nmis_legacy():
    """Legacy way of reading in data"""
    meter_data = read_nem_file("examples/unzipped/Example_NEM12_actual_interval.csv")
    assert len(meter_data.readings) == 1
    assert "VABD000163" in meter_data.readings
