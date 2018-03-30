""" Test Suite
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
import nemreader as nr


def test_unzipped_examples():
    """ Open and parse unzipped example files """

    test_path = os.path.abspath('examples/unzipped')
    for file_name in os.listdir(test_path):
        test_file = os.path.join(test_path, file_name)
        meter_data = nr.read_nem_file(test_file)
        assert meter_data.header.version_header in ['NEM12', 'NEM13']


def test_nem12_examples():
    """ Open and parse zipped NEM12 example files """
    skips = [
            'NEM12#Scenario10#ETSAMDP#NEMMCO.zip', # 300 Row has new line
            ]
    test_path = os.path.abspath('examples/nem12')
    for file_name in os.listdir(test_path):
        if file_name in skips:
            continue
        test_file = os.path.join(test_path, file_name)
        meter_data = nr.read_nem_file(test_file)
        assert meter_data.header.version_header in ['NEM12', 'NEM13']


def test_nem13_examples():
    """ Open and parse zipped NEM13 example files """

    test_path = os.path.abspath('examples/nem13')
    for file_name in os.listdir(test_path):
        test_file = os.path.join(test_path, file_name)
        meter_data = nr.read_nem_file(test_file)
        assert meter_data.header.version_header in ['NEM12', 'NEM13']
