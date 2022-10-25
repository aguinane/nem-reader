from nemreader import NEMFile


def test_optional_scheduled_read():
    nf = NEMFile("examples/unzipped/Example_NEM12_no_scheduled_read.csv", strict=True)
    meter_data = nf.nem_data()
    readings = meter_data.readings["NMI111"]["E1"]
    assert len(readings) == 96
