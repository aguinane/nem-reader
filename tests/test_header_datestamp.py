import datetime

from nemreader import NEMFile


def test_Date12_parse():
    """test that Date12 is parsed correctly"""
    # 200402070911 = 2004-02-07, 09:11
    nf = NEMFile("examples/unzipped/Example_NEM12_multiple_meters.csv", strict=True)
    meter_data = nf.nem_data()
    assert meter_data.header.creation_date == datetime.datetime(2004, 2, 7, 9, 11)
