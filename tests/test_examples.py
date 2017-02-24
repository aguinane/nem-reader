""" Test Suite
"""

import unittest
import nemreader as nr


class TestReadings(unittest.TestCase):
    """ Test reading tuples are returned correctly """

    def test_nem12_records(self):
        """ Test example NEM12 file """
        meter_data = nr.read_nem_file('examples/Example_NEM12_actual_interval.csv')
        records = meter_data.readings['VABD000163']['E1']
        unit_count = 0
        for record in records:
            unit_count += record[2] # Read value should be third record in tuple
        self.assertAlmostEqual(unit_count, 1.111*24*2, places=1)

    def test_nem12_records_quality_flag(self):
        """ Test example NEM12 file with quality flags

        Quality flags should be set correctly
        """
        meter_data = nr.read_nem_file('examples/Example_NEM12_multiple_quality.csv')
        records = meter_data.readings['CCCC123456']['E1']
        unit_count = 0
        unit_count_actual = 0
        for record in records:
            unit_count += record[2] # Read value should be third record in tuple
            # Only four records have an 'A' flag in the example
            if record.quality_method == 'A':
                unit_count_actual += record.read_value
        self.assertAlmostEqual(unit_count_actual, 74.112, places=1)
        self.assertAlmostEqual(unit_count, 896.99, places=1)


    def test_nem13_records(self):
        """ Test example NEM13 file """
        meter_data = nr.read_nem_file('examples/Example_NEM13_consumption_data.csv')
        records = meter_data.readings['VABC005890']['11']
        unit_count = 0
        for record in records:
            unit_count += record[2] # Read value should be third record in tuple
        self.assertAlmostEqual(unit_count, 1312.1, places=1)
