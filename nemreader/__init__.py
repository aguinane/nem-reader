"""
    nemreader
    ~~~~~
    Parse AEMO NEM12 (interval metering data) and
    NEM13 (accumulated metering data) data files
"""

from .nem_reader import read_nem_file, parse_nem_file
