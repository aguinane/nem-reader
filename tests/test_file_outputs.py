""" Test Suite
"""

import pytest
import os
import sys
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nemreader import output_as_csv


def test_correct_NMIs(tmpdir):
    """ Create a temporary csv output """
    file_name = 'examples/unzipped/Example_NEM12_actual_interval.csv'
    output_path = tmpdir + 'test_output.csv'
    output_file = output_as_csv(file_name, output_file=output_path)
    print(output_file)
    assert output_file == output_path
