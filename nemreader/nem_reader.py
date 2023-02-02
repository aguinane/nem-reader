import csv
import logging
import os
import zipfile
from datetime import datetime, timedelta
from itertools import chain, islice
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple

import pandas as pd

from .nem_objects import (
    B2BDetails12,
    B2BDetails13,
    BasicMeterData,
    EventRecord,
    HeaderRecord,
    IntervalRecord,
    NEMData,
    NEMReadings,
    NmiDetails,
    Reading,
)
from .split_days import make_set_interval, split_multiday_reads

log = logging.getLogger(__name__)


class NEMFile:
    """An NEM file object"""

    def __init__(self, file_path: str, strict: bool = False) -> None:

        self.file_path = file_path
        self.strict = strict
        self.nmis: set = set()
        self.nmi_channels: dict = {}

    def __repr__(self):
        return f"<NEMFile {self.file_path}>"

    @property
    def zipped(self) -> bool:
        """Check whether file is zipped or not"""
        _, file_extension = os.path.splitext(self.file_path)
        if file_extension.lower() == ".zip":
            return True
        return False

    def parse_nem_file(self, nem_file, file_name="") -> NEMReadings:
        """Parse NEM file and return meter readings named tuple"""
        reader = csv.reader(nem_file, delimiter=",")
        first_row = next(reader, None)

        # Some Powercor/Citipower files have empty line at start, skip if so.
        if not first_row:
            first_row = next(reader, None)

        try:
            record_indicator = int(first_row[0])
        except Exception:
            record_indicator = 0

        if not first_row or record_indicator != 100:
            if self.strict:
                raise ValueError("NEM Files must start with a 100 row")
            else:
                log.warning("Missing header (100) row, assuming NEM12.")
                header = HeaderRecord("NEM12", None, "", "", file_name, assumed=True)
        else:
            header = parse_100_row(first_row, file_name)
            if header.version_header not in ["NEM12", "NEM13"]:
                raise ValueError("Invalid NEM version {}".format(header.version_header))

        self.header = header
        if header.assumed:
            # We have to parse the first row again so we don't miss any data.
            reader = chain([first_row], reader)
            return parse_nem12_rows(reader, file_name=nem_file)
        if header.version_header == "NEM12":
            return parse_nem12_rows(reader, file_name=nem_file)
        else:
            return parse_nem13_rows(reader)

    def nem_data(self) -> NEMData:
        """Return data in legacy data format"""
        if self.zipped:
            log.debug("Extracting zip file")
            with zipfile.ZipFile(self.file_path, "r") as archive:
                files = archive.namelist()
                if len(files) > 1:
                    raise ValueError("Only zip files with one file are supported")
                csv_file = files[0]
                with archive.open(csv_file) as csv_text:
                    # Zip file is open in binary mode
                    # So decode then convert back to list
                    nmi_file = csv_text.read().decode("utf-8").splitlines()
                    reads = self.parse_nem_file(nmi_file, file_name=csv_file)
                    for nmi in reads.transactions.keys():
                        self.nmis.add(nmi)
                        suffixes = list(reads.transactions[nmi].keys())
                        self.nmi_channels[nmi] = suffixes
                    return NEMData(
                        header=self.header,
                        readings=reads.readings,
                        transactions=reads.transactions,
                    )

        with open(self.file_path) as nmi_file:
            reads = self.parse_nem_file(nmi_file)
            for nmi in reads.transactions.keys():
                self.nmis.add(nmi)
                suffixes = list(reads.transactions[nmi].keys())
                self.nmi_channels[nmi] = suffixes
            return NEMData(
                header=self.header,
                readings=reads.readings,
                transactions=reads.transactions,
            )

    def get_data_frame(
        self, split_days: bool = False, set_interval: Optional[int] = None
    ) -> pd.DataFrame:
        """Return NEMData as a DataFrame"""
        nd = self.nem_data()
        frames = []
        for nmi in nd.readings.keys():
            for suffix in nd.readings[nmi].keys():
                reads = nd.readings[nmi][suffix]

                if split_days or set_interval:
                    reads = list(split_multiday_reads(reads))

                if set_interval:
                    reads = list(make_set_interval(reads, set_interval))

                data = {
                    "nmi": [nmi for _ in range(len(reads))],
                    "suffix": [suffix for _ in range(len(reads))],
                    "serno": [x.meter_serial_number for x in reads],
                    "t_start": [x.t_start for x in reads],
                    "t_end": [x.t_end for x in reads],
                    "value": [x.read_value for x in reads],
                    "quality": [x.quality_method for x in reads],
                    "evt_code": [x.event_code for x in reads],
                    "evt_desc": [x.event_desc for x in reads],
                }
                frames.append(pd.DataFrame(data))
        return pd.concat(frames)

    def get_pivot_data_frame(
        self,
        split_days: bool = False,
        set_interval: Optional[int] = None,
        include_serno: bool = False,
    ) -> pd.DataFrame:
        """Return NEMData as a DataFrame with suffix columns"""
        df = self.get_data_frame(split_days, set_interval)
        pivot_index = ["nmi", "t_start", "t_end", "quality", "evt_code", "evt_desc"]
        if include_serno:
            pivot_index.append("serno")
        df_pivoted = df.pivot(
            index=pivot_index,
            columns="suffix",
            values="value",
        ).reset_index()
        return df_pivoted

    def get_per_nmi_dfs(
        self,
        split_days: bool = False,
        set_interval: Optional[int] = None,
        include_serno: bool = False,
    ) -> Generator[Tuple[str, pd.DataFrame], None, None]:
        df = self.get_pivot_data_frame(split_days, set_interval, include_serno)
        nmis = df.nmi.unique()
        for nmi in nmis:
            nmi_df = df[(df["nmi"] == nmi)]
            del nmi_df["nmi"]
            yield nmi, nmi_df


def flatten_list(l: List[list]) -> list:
    """takes a list of lists, l and returns a flat list"""
    return [v for inner_l in l for v in inner_l]


def read_nem_file(file_path: str, ignore_missing_header=False) -> NEMData:
    """Read in NEM file and return meter readings named tuple

    :param file_path: The NEM file to process
    :param ignore_missing_header: Whether to continue parsing if missing header.
                                  Will assume NEM12 format.
    :returns: The file that was created
    """

    nf = NEMFile(file_path, strict=ignore_missing_header)
    return nf.nem_data()


def parse_100_row(row: List[Any], file_name: str) -> HeaderRecord:
    """Parse header record (100)"""
    return HeaderRecord(
        row[1], parse_datetime(row[2]), row[3], row[4], file_name, False
    )


def parse_nem12_rows(nem_list: Iterable, file_name=None) -> NEMReadings:
    """Parse NEM row iterator and return meter readings named tuple"""
    # readings nested by NMI then channel
    readings: Dict[str, Dict[str, List[Reading]]] = {}
    # transactions nested by NMI then channel
    trans: Dict[str, Dict[str, list]] = {}
    nmi_d = None  # current NMI details block that readings apply to

    observed_900_record = False

    for row in nem_list:

        if not row:
            log.debug("Skipping empty row.")
            continue

        record_indicator = int(row[0])

        if record_indicator == 900:
            # Powercor NEM12 files can concatenate multiple files together
            # try to keep parsing anyway.
            if observed_900_record:
                log.warning("Found multiple end of data (900) rows. ")

            observed_900_record = True
            pass

        elif record_indicator == 200:
            try:
                nmi_details = parse_200_row(row)
            except ValueError:
                log.error("Error passing 200 row:")
                log.error(row)
                raise
            nmi_d = nmi_details

            if nmi_d.nmi not in readings:
                readings[nmi_d.nmi] = {}
            if nmi_d.nmi_suffix not in readings[nmi_d.nmi]:
                readings[nmi_d.nmi][nmi_d.nmi_suffix] = []
            if nmi_d.nmi not in trans:
                trans[nmi_d.nmi] = {}
            if nmi_d.nmi_suffix not in trans[nmi_d.nmi]:
                trans[nmi_d.nmi][nmi_d.nmi_suffix] = []

        elif record_indicator == 300:
            num_intervals = int(24 * 60 / nmi_d.interval_length)
            assert len(row) > 1, f"Invalid 300 Row in {file_name}"
            if len(row) < num_intervals + 2:
                record_date = row[1]
                msg = "Skipping 300 record for %s %s %s. "
                msg += "It does not have the expected %s intervals"
                log.error(msg, nmi_d.nmi, nmi_d.nmi_suffix, record_date, num_intervals)
                continue
            interval_record = parse_300_row(
                row, nmi_d.interval_length, nmi_d.uom, nmi_d.meter_serial_number
            )
            # don't flatten the list of interval readings at this stage,
            # as they may need to be adjusted by a 400 row
            readings[nmi_d.nmi][nmi_d.nmi_suffix].append(
                interval_record.interval_values
            )

        elif record_indicator == 400:
            event_record = parse_400_row(row)
            readings[nmi_d.nmi][nmi_d.nmi_suffix][-1] = update_reading_events(
                readings[nmi_d.nmi][nmi_d.nmi_suffix][-1], event_record
            )

        elif record_indicator == 500:
            b2b_details = parse_500_row(row)
            trans[nmi_d.nmi][nmi_d.nmi_suffix].append(b2b_details)

        else:
            log.warning(
                "Record indicator %s not supported and was skipped", record_indicator
            )

    for nmi in readings:
        for suffix in readings[nmi]:
            readings[nmi][suffix] = flatten_list(readings[nmi][suffix])

    if not observed_900_record:
        log.warning("Missing end of data (900) row.")

    return NEMReadings(readings=readings, transactions=trans)


def parse_nem13_rows(nem_list: Iterable) -> NEMReadings:
    """Parse NEM row iterator and return meter readings named tuple"""
    # readings nested by NMI then channel
    readings: Dict[str, Dict[str, List[Reading]]] = {}
    # transactions nested by NMI then channel
    trans: Dict[str, Dict[str, list]] = {}
    nmi_d = None  # current NMI details block that readings apply to

    for row in nem_list:
        record_indicator = int(row[0])

        if record_indicator == 900:
            for nmi in readings:
                for suffix in readings[nmi]:
                    readings[nmi][suffix] = flatten_list(readings[nmi][suffix])
            break  # End of file

        elif record_indicator == 550:
            b2b_details = parse_550_row(row)
            trans[nmi_d.nmi][nmi_d.nmi_suffix].append(b2b_details)

        elif record_indicator == 250:
            basic_data = parse_250_row(row)
            reading = calculate_manual_reading(basic_data)

            nmi_d = basic_data

            if basic_data.nmi not in readings:
                readings[nmi_d.nmi] = {}
            if nmi_d.nmi_suffix not in readings[nmi_d.nmi]:
                readings[nmi_d.nmi][nmi_d.nmi_suffix] = []
            if nmi_d.nmi not in trans:
                trans[nmi_d.nmi] = {}
            if nmi_d.nmi_suffix not in trans[nmi_d.nmi]:
                trans[nmi_d.nmi][nmi_d.nmi_suffix] = []

            readings[nmi_d.nmi][nmi_d.nmi_suffix].append([reading])

        else:
            log.warning(
                "Record indicator %s not supported and was skipped", record_indicator
            )
    return NEMReadings(readings=readings, transactions=trans)


def calculate_manual_reading(basic_data: BasicMeterData) -> Reading:
    """Calculate the interval between two manual readings"""
    t_start = basic_data.previous_register_read_datetime
    t_end = basic_data.current_register_read_datetime
    val_start = basic_data.previous_register_read
    val_end = basic_data.current_register_read
    value = basic_data.quantity

    meter_serial_number = basic_data.meter_serial_number
    uom = basic_data.uom
    quality_method = basic_data.current_quality_method

    return Reading(
        t_start,
        t_end,
        value,
        uom,
        meter_serial_number,
        quality_method,
        "",
        "",
        val_start,
        val_end,
    )


def parse_200_row(row: list) -> NmiDetails:
    """Parse NMI data details record (200)"""

    next_read = None  # Next scheduled read is an optional field
    if len(row) > 9:
        next_read = parse_datetime(row[9])

    return NmiDetails(
        row[1], row[2], row[3], row[4], row[5], row[6], row[7], int(row[8]), next_read
    )


def parse_250_row(row: list) -> BasicMeterData:
    """Parse basic meter data record (250)"""
    return BasicMeterData(
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
        row[6],
        row[7],
        float(row[8]),
        parse_datetime(row[9]),
        row[10],
        row[11],
        row[12],
        float(row[13]),
        parse_datetime(row[14]),
        row[15],
        row[16],
        row[17],
        float(row[18]),
        row[19],
        row[20],
        parse_datetime(row[21]),
        parse_datetime(row[22]),
    )


def nth(iterable, n, default=None):
    "Returns the nth item or a default value"
    return next(islice(iterable, n, None), default)


def parse_300_row(
    row: list, interval: int, uom: str, meter_serial_number: str
) -> IntervalRecord:
    """Interval data record (300)"""

    num_intervals = int(24 * 60 / interval)
    interval_date = parse_datetime(row[1])
    last_interval = 2 + num_intervals
    quality_method = row[last_interval]

    # Optional fields
    reason_code = nth(row, last_interval + 1, "")
    reason_desc = nth(row, last_interval + 2, "")
    update_datetime = parse_datetime(nth(row, last_interval + 3, None))
    msats_load_datatime = parse_datetime(nth(row, last_interval + 4, None))

    interval_values = parse_interval_records(
        row[2:last_interval],
        interval_date,
        interval,
        uom,
        quality_method,
        meter_serial_number,
        reason_code,
        reason_desc,
    )
    return IntervalRecord(
        interval_date,
        interval_values,
        quality_method,
        meter_serial_number,
        reason_code,
        reason_desc,
        update_datetime,
        msats_load_datatime,
    )


def parse_interval_records(
    interval_record,
    interval_date,
    interval,
    uom,
    quality_method,
    meter_serial_number,
    event_code: str = "",
    event_desc: str = "",
) -> List[Reading]:
    """Convert interval values into tuples with datetime"""
    interval_delta = timedelta(minutes=interval)
    return [
        Reading(
            t_start=interval_date + (i * interval_delta),
            t_end=interval_date + (i * interval_delta) + interval_delta,
            read_value=parse_reading(val),
            uom=uom,
            quality_method=quality_method,
            meter_serial_number=meter_serial_number,
            event_code=event_code,  # This may get changed later by a 400 row
            event_desc=event_desc,  # This may get changed later by a 400 row
            val_start=None,
            val_end=None,  # No before and after readings for intervals
        )
        for i, val in enumerate(interval_record)
    ]


def parse_reading(val: str) -> Optional[float]:
    """Convert reading value to float (if possible)"""
    if val == "":
        return None
    try:
        return float(val)
    except ValueError:
        log.warning('Reading of "%s" is not a number', val)
        return None  # Not a valid reading


def parse_400_row(row: list) -> tuple:
    """Interval event record (400)"""

    return EventRecord(int(row[1]), int(row[2]), row[3], row[4], row[5])


def update_reading_events(readings, event_record):
    """Updates readings from a 300 row to reflect any events found in a
    subsequent 400 row
    """
    # event intervals are 1-indexed
    for i in range(event_record.start_interval - 1, event_record.end_interval):
        readings[i] = Reading(
            t_start=readings[i].t_start,
            t_end=readings[i].t_end,
            read_value=readings[i].read_value,
            uom=readings[i].uom,
            meter_serial_number=readings[i].meter_serial_number,
            quality_method=event_record.quality_method,
            event_code=event_record.reason_code,
            event_desc=event_record.reason_description,
            val_start=readings[i].val_start,
            val_end=readings[i].val_end,
        )
    return readings


def parse_500_row(row: list) -> tuple:
    """Parse B2B details record"""
    return B2BDetails12(row[1], row[2], row[3], row[4])


def parse_550_row(row: list) -> tuple:
    """Parse B2B details record"""
    return B2BDetails13(row[1], row[2], row[3], row[4])


def parse_datetime(record: str) -> Optional[datetime]:
    """Parse a datetime string into a python datetime object"""
    # NEM defines Date8, DateTime12 and DateTime14
    format_strings = {8: "%Y%m%d", 12: "%Y%m%d%H%M", 14: "%Y%m%d%H%M%S"}

    if record == "" or record is None:
        return None

    try:
        timestamp = datetime.strptime(
            record.strip(), format_strings[len(record.strip())]
        )
    except (ValueError, KeyError):
        log.debug(f"Malformed date '{record}' ")
        return None

    return timestamp
