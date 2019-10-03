"""
    nemreader.outputs
    ~~~~~
    Output results in different formats
"""

import os
import logging
import csv
from typing import Generator, Tuple, List
from pathlib import Path
from .nem_reader import read_nem_file

log = logging.getLogger(__name__)


def nmis_in_file(file_name) -> Generator[Tuple[str, List[str]], None, None]:
    """ Return list of NMIs in file """
    m = read_nem_file(file_name)
    for nmi in m.transactions.keys():
        suffixes = list(m.transactions[nmi].keys())
        yield nmi, suffixes


def output_as_csv(file_name, output_dir="."):
    """
    Transpose all channels and output a csv that is easier
    to read and do charting on

    :param file_name: The NEM file to process
    :param output_dir: Specify different output location
    :returns: The file that was created
    """

    output_dir = Path(output_dir)
    output_paths = []
    os.makedirs(output_dir, exist_ok=True)
    m = read_nem_file(file_name)
    nmis = m.readings.keys()
    for nmi in nmis:
        channels = list(m.transactions[nmi].keys())
        num_records = len(m.readings[nmi][channels[0]])
        last_date = m.readings[nmi][channels[0]][-1].t_end
        output_file = "{}_{}_transposed.csv".format(nmi, last_date.strftime("%Y%m%d"))
        output_path = output_dir / output_file
        with open(output_path, "w", newline="") as csvfile:
            cwriter = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            heading_list = ["period_start", "period_end"]
            for channel in channels:
                heading_list.append(channel)
            heading_list.append("quality_method")
            heading_list.append("event")
            cwriter.writerow(heading_list)

            for i in range(0, num_records):
                t_start = m.readings[nmi][channels[0]][i].t_start
                t_end = m.readings[nmi][channels[0]][i].t_end
                quality_method = m.readings[nmi][channels[0]][i].quality_method
                event_code = m.readings[nmi][channels[0]][i].event_code
                event_desc = m.readings[nmi][channels[0]][i].event_desc
                row_list = [t_start, t_end]
                for ch in channels:
                    val = m.readings[nmi][ch][i].read_value
                    row_list.append(val)
                row_list.append(quality_method)
                row_list.append(f"{event_code} {event_desc}")
                cwriter.writerow(row_list)
        log.debug("Created %s", output_path)
        output_paths.append(output_path)
    return output_paths
