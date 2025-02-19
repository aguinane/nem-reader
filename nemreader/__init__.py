"""
nemreader
~~~~~
Parse AEMO NEM12 (interval metering data) and
NEM13 (accumulated metering data) data files
"""

import logging
from logging import NullHandler

from .nem_reader import NEMFile, read_nem_file
from .output_db import extend_sqlite, output_as_sqlite, output_folder_as_sqlite
from .outputs import (
    nmis_in_file,
    output_as_csv,
    output_as_daily_csv,
    output_as_data_frames,
)
from .version import __version__

__all__ = [
    "NEMFile",
    "__version__",
    "extend_sqlite",
    "nmis_in_file",
    "output_as_csv",
    "output_as_daily_csv",
    "output_as_data_frames",
    "output_as_sqlite",
    "output_folder_as_sqlite",
    "read_nem_file",
]

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())
