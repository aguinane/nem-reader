"""
    nemreader.outputs
    ~~~~~
    Output results in different formats
"""

import os
import logging
import csv
from typing import Generator, Tuple, List, Dict, Any
from pathlib import Path
from .nem_objects import Reading
from .nem_reader import read_nem_file
from .split_days import split_multiday_reads

log = logging.getLogger(__name__)


def nmis_in_file(file_name) -> Generator[Tuple[str, List[str]], None, None]:
    """ Return list of NMIs in file """
    m = read_nem_file(file_name)
    for nmi in m.transactions.keys():
        suffixes = list(m.transactions[nmi].keys())
        yield nmi, suffixes


def flatten_rows(
    nmi_transactions: Dict[str, list],
    nmi_readings: Dict[str, List[Reading]],
    split_days: bool = False,
) -> Tuple[List[str], List[list]]:
    """ Create flattened list of NMI reading data """

    channels = list(nmi_transactions.keys())
    if split_days:
        # Split any readings that are >24 hours
        for ch in channels:
            nmi_readings[ch] = list(split_multiday_reads(nmi_readings[ch]))

    headings = ["period_start", "period_end"]
    for channel in channels:
        headings.append(channel)
    headings.append("quality_method")
    headings.append("event")

    rows = []
    num_records = len(nmi_readings[channels[0]])
    first_ch = channels[0]
    for i in range(0, num_records):
        t_start = nmi_readings[first_ch][i].t_start
        t_end = nmi_readings[first_ch][i].t_end
        quality_method = nmi_readings[first_ch][i].quality_method
        event_code = nmi_readings[first_ch][i].event_code
        event_desc = nmi_readings[first_ch][i].event_desc
        row: List[Any] = [t_start, t_end]
        for ch in channels:
            try:
                val = nmi_readings[ch][i].read_value
            except IndexError:
                val = None
            row.append(val)
        row.append(quality_method)
        row.append(f"{event_code} {event_desc}")
        rows.append(row)
    return headings, rows


def output_as_data_frames(file_name, split_days: bool = True):
    """ Return list of data frames for each NMI """

    import pandas as pd

    m = read_nem_file(file_name)
    nmis = list(m.readings.keys())
    data_frames = []
    for nmi in nmis:
        nmi_readings = m.readings[nmi]
        headings, rows = flatten_rows(m.transactions[nmi], nmi_readings, split_days)
        nmi_df = pd.DataFrame(data=rows, columns=headings)
        data_frames.append((nmi, nmi_df))

    return data_frames


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
        headings, rows = flatten_rows(m.transactions[nmi], m.readings[nmi])
        last_date = rows[-1][1]
        output_file = "{}_{}_transposed.csv".format(nmi, last_date.strftime("%Y%m%d"))
        output_path = output_dir / output_file
        save_to_csv(headings, rows, output_path)
        output_paths.append(output_path)
    return output_paths


def save_to_csv(headings: List[str], rows: List[list], output_path):
    """ save data to csv file """
    with open(output_path, "w", newline="") as csvfile:
        cwriter = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        cwriter.writerow(headings)
        for row in rows:
            cwriter.writerow(row)
    log.debug("Created %s", output_path)
    return output_path


def flatten_and_group_rows(
    nmi: str,
    nmi_transactions: Dict[str, list],
    nmi_readings: Dict[str, List[Reading]],
    date_format: str = "%Y%m%d",
) -> List[list]:
    """ Create flattened list of NMI reading data """

    channels = list(nmi_transactions.keys())

    # Datastream suffix starting with a number are Accumulated Metering Data (NEM13)
    # Ensure no reading exceeds 24 hours
    split_required = False
    for ch in channels:
        if ch[0].isdigit():
            split_required = True
    if split_required:
        nmi_readings = split_multiday_reads(nmi_readings)

    rows = []
    for ch in channels:
        date_totals = {}
        date_qualities = {}
        uom = ""
        sn = ""
        for read in nmi_readings[ch]:
            t_end = read.t_start
            val = read.read_value
            uom = read.uom  # Only last value will be saved
            sn = read.meter_serial_number
            quality = read.quality_method
            t_group = t_end.strftime(date_format)
            try:
                date_totals[t_group] += val
            except KeyError:
                date_totals[t_group] = val

            if t_group not in date_qualities.keys():
                date_qualities[t_group] = set()
            date_qualities[t_group].add(quality)

        for day in date_totals.keys():
            day_total = date_totals[day]
            qualities = list(date_qualities[day])
            day_quality = "".join(qualities)
            if len(day_quality) > 1:
                day_quality = "V"  # Multiple quality methods
            row: List[Any] = [nmi, sn, day, ch, day_total, uom, day_quality]
            rows.append(row)
    return rows


def output_as_daily_csv(file_name, output_dir="."):
    """
    Transpose all channels and output a daily csv that is easier
    to read and do charting on

    :param file_name: The NEM file to process
    :param output_dir: Specify different output location
    :returns: The file that was created
    """

    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    file_stem = Path(file_name).stem
    output_file = "{}_daily_totals.csv".format(file_stem)
    output_path = output_dir / output_file

    m = read_nem_file(file_name)
    nmis = m.readings.keys()
    all_rows = []
    headings = [
        "nmi",
        "meter_sn",
        "day",
        "channel",
        "day_total",
        "uom",
        "quality_method",
    ]
    for nmi in nmis:
        rows = flatten_and_group_rows(nmi, m.transactions[nmi], m.readings[nmi])
        for row in rows:
            all_rows.append(row)

    save_to_csv(headings, all_rows, output_path)

    return output_path
