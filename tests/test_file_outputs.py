""" Test Suite
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from nemreader import output_as_csv


def test_csv_output(tmpdir):
    """ Create a temporary csv output """
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_files = output_as_csv(file_name, output_dir=tmpdir)
    assert len(output_files) == 1
