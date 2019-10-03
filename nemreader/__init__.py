"""
    nemreader
    ~~~~~
    Parse AEMO NEM12 (interval metering data) and
    NEM13 (accumulated metering data) data files
"""

import logging
from logging import NullHandler

from .version import __version__
from .nem_reader import read_nem_file, parse_nem_file
from .outputs import output_as_csv
from .outputs import nmis_in_file

__all__ = [
    "__version__",
    "read_nem_file",
    "parse_nem_file",
    "output_as_csv",
    "nmis_in_file",
]

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())
