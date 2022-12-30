import csv
import logging
import os
import warnings
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import pandas as pd
from sqlite_utils import Database

from .nem_objects import Reading
from .nem_reader import NEMFile
from .split_days import make_set_interval, split_multiday_reads

log = logging.getLogger(__name__)


def nmis_in_file(file_name) -> Generator[Tuple[str, List[str]], None, None]:
    """Return list of NMIs in file"""
    nf = NEMFile(file_name, strict=False)
    nf.nem_data()
    for nmi, suffixes in nf.nmi_channels.items():
        yield nmi, suffixes


def get_data_frame(
    channels: List[str],
    nmi_readings: Dict[str, List[Reading]],
    split_days: bool = False,
    set_interval: Optional[int] = None,
) -> pd.DataFrame:
    """Get a Pandas DataFrame for NMI"""

    warnings.warn("nemreader.get_data_frame is deprecated`.", DeprecationWarning)

    if split_days or set_interval:
        # Split any readings that are >24 hours
        for ch in channels:
            nmi_readings[ch] = list(split_multiday_reads(nmi_readings[ch]))

    if set_interval:
        for ch in channels:
            nmi_readings[ch] = list(make_set_interval(nmi_readings[ch], set_interval))

    # Work out which channel has smallest intervals and use that as first index
    ch_rows = []
    for i, ch in enumerate(channels):
        num_rows = len(nmi_readings[ch])
        ch_rows.append((num_rows, ch))
    ch_rows.sort()
    first_ch = ch_rows[-1][1]

    d = {
        "t_start": [x.t_start for x in nmi_readings[first_ch]],
        "t_end": [x.t_end for x in nmi_readings[first_ch]],
        "quality_method": [x.quality_method for x in nmi_readings[first_ch]],
        "event_code": [x.event_code for x in nmi_readings[first_ch]],
        "event_desc": [x.event_desc for x in nmi_readings[first_ch]],
    }
    d[first_ch] = [x.read_value for x in nmi_readings[first_ch]]

    df = pd.DataFrame(data=d, index=d["t_start"])

    for ch in channels:
        if ch == first_ch:
            continue  # This channel already added
        index = [x.t_start for x in nmi_readings[ch]]
        values = [x.read_value for x in nmi_readings[ch]]
        ser = pd.Series(data=values, index=index, name=ch)
        df.loc[:, ch] = ser
    return df


def output_as_data_frames(
    file_name,
    split_days: bool = True,
    set_interval: Optional[int] = None,
    strict: bool = False,
) -> List[Tuple[str, pd.DataFrame]]:
    """Return list of data frames for each NMI"""
    nf = NEMFile(file_name, strict=strict)
    data_frames = []
    for nmi, nmi_df in nf.get_per_nmi_dfs(
        split_days=split_days, set_interval=set_interval
    ):
        nmi_df.rename(columns={"quality": "quality_method"}, inplace=True)
        data_frames.append((nmi, nmi_df))
    return data_frames


def output_as_csv(file_name, output_dir=".", set_interval: Optional[int] = None):
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
    nf = NEMFile(file_name, strict=False)
    df = nf.get_pivot_data_frame(set_interval=set_interval)
    for nmi in nf.nmis:
        nmi_df = df[(df["nmi"] == nmi)]
        del nmi_df["nmi"]
        last_date = nmi_df.iloc[-1][1].strftime("%Y%m%d")
        output_file = f"{nmi}_{last_date}_transposed.csv"
        output_path = output_dir / output_file
        nmi_df.to_csv(output_path, index=False)
        output_paths.append(output_path)
    return output_paths


def save_to_csv(headings: List[str], rows: List[list], output_path):
    """save data to csv file"""
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
    """Create flattened list of NMI reading data"""

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
    output_file = f"{file_stem}_daily_totals.csv"
    output_path = output_dir / output_file

    nf = NEMFile(file_name, strict=False)
    m = nf.nem_data()
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


def output_as_sqlite(
    file_name: Path,
    output_dir=".",
    split_days: bool = False,
    set_interval: Optional[int] = None,
):
    """Export all channels to sqlite file"""

    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_path = output_dir / "nemdata.db"
    db = Database(output_path)

    nf = NEMFile(file_name, strict=False)
    m = nf.nem_data()
    nmis = m.readings.keys()
    for nmi in nmis:
        channels = list(m.transactions[nmi].keys())
        nmi_readings = m.readings[nmi]

        for ch in channels:
            if split_days or set_interval:
                nmi_readings[ch] = list(split_multiday_reads(nmi_readings[ch]))

            if set_interval:
                nmi_readings[ch] = list(
                    make_set_interval(nmi_readings[ch], set_interval)
                )

            items = []
            for x in nmi_readings[ch]:
                item = {
                    "nmi": nmi,
                    "channel": ch,
                    "t_start": x.t_start,
                    "t_end": x.t_end,
                    "value": x.read_value,
                    "quality_method": x.quality_method,
                    "event_code": x.event_code,
                    "event_desc": x.event_desc,
                }
                items.append(item)
            db["readings"].upsert_all(
                items,
                pk=("nmi", "channel", "t_start"),
                column_order=("nmi", "channel", "t_start"),
            )

    db.create_view(
        "nmi_summary",
        """
        SELECT nmi, channel, MIN(t_start) as first_interval, MAX(t_end) as last_interval
        FROM readings
        GROUP BY nmi, channel
    """,
        replace=True,
    )
    return output_path
