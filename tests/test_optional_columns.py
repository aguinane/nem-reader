import nemreader as nr


def test_optional_scheduled_read():
    meter_data = nr.read_nem_file(
        "examples/unzipped/Example_NEM12_no_scheduled_read.csv"
    )
    readings = meter_data.readings["NMI111"]["E1"]
    assert len(readings) == 96
