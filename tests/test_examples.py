""" Test Suite 
""" 
 
import unittest 
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
import nemreader as nr


class TestNEM12ActualIntervals(unittest.TestCase):
    """ Test the actual intervals example """
    def setUp(self):
        self.meter_data = nr.read_nem_file('examples/Example_NEM12_actual_interval.csv')

    def test_correct_NMIs(self):
        # only 1 NMI
        self.assertEqual(len(self.meter_data.readings), 1)
        self.assertIn('VABD000163', self.meter_data.readings)

    def test_correct_channels(self):
        readings = self.meter_data.readings['VABD000163']
        self.assertEqual(len(readings), 2)
        self.assertIn('E1', readings)
        self.assertIn('Q1', readings)

    def test_correct_records(self):
        readings = self.meter_data.readings['VABD000163']
        self.assertEqual(len(readings['E1']), 48)
        self.assertAlmostEqual(readings['E1'][10].read_value, 1.11, places=2)
        self.assertAlmostEqual(readings['E1'][-1].read_value, 1.11, places=2)
        self.assertEqual(len(readings['Q1']), 48)
        self.assertAlmostEqual(readings['Q1'][10].read_value, 2.22, places=2)
        self.assertAlmostEqual(readings['Q1'][-1].read_value, 2.22, places=2)
        self.assertEqual(readings['Q1'][-1].quality_method, 'A')


class TestNEM12MultipleQuality(unittest.TestCase):
    """ Test the actual intervals example
    """
    def setUp(self):
        self.meter_data = nr.read_nem_file('examples/Example_NEM12_multiple_quality.csv')

    def test_correct_records(self):
        readings = self.meter_data.readings['CCCC123456']['E1']
        self.assertEqual(len(readings), 48)
        self.assertAlmostEqual(readings[0].read_value, 18.023, places=3)
        self.assertAlmostEqual(readings[-1].read_value, 14.733, places=3)

    def test_correct_quality(self):
        readings = self.meter_data.readings['CCCC123456']['E1']
        self.assertEqual(readings[0].quality_method, 'F14')
        self.assertEqual(readings[10].quality_method, 'F14')
        self.assertEqual(readings[19].quality_method, 'F14')
        self.assertEqual(readings[20].quality_method, 'A')
        self.assertEqual(readings[22].quality_method, 'A')
        self.assertEqual(readings[23].quality_method, 'A')
        self.assertEqual(readings[25].quality_method, 'S14')
        self.assertEqual(readings[30].quality_method, 'S14')
        self.assertEqual(readings[47].quality_method, 'S14')


class TestNEM13Consumption(unittest.TestCase):
    """ Test the NEM13 consumption data
    """
    def setUp(self):
        self.meter_data = nr.read_nem_file('examples/Example_NEM13_consumption_data.csv')

    def test_nem13_readings(self):
        readings = self.meter_data.readings['VABC005890']['11']
        unit_count = 0
        for record in readings:
            unit_count += record[2] # Read value should be third record in tuple
        self.assertAlmostEqual(unit_count, 1312.1, places=1)
