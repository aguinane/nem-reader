""" Test Suite
"""

import os
import sys
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import nemreader as nr


def test_Date12_parse():
    """ test that Date12 is parsed correctly """
    # 200402070911 = 2004-02-07, 09:11
    meter_data = nr.read_nem_file(
        os.path.abspath("examples/unzipped/Example_NEM12_multiple_meters.csv")
    )
    assert meter_data.header.creation_date == datetime.datetime(2004, 2, 7, 9, 11)
