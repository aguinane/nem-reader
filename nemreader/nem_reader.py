"""
    nemreader.nem_reader
    ~~~~~
    Read MDFF format
"""

import os
import csv
import logging
from datetime import datetime, timedelta
import zipfile
from itertools import chain, islice
from typing import Iterable, Any
from typing import Optional, List, Dict
from .nem_objects import NEMFile, HeaderRecord, NmiDetails
from .nem_objects import Reading, BasicMeterData, IntervalRecord, EventRecord
from .nem_objects import B2BDetails12, B2BDetails13

log = logging.getLogger(__name__)


def flatten_list(l: List[list]) -> list:
    """ takes a list of lists, l and returns a flat list
    """
    return [v for inner_l in l for v in inner_l]


def read_nem_file(file_path: str, ignore_missing_header=False) -> NEMFile:
    """ Read in NEM file and return meter readings named tuple

    :param file_path: The NEM file to process
    :param ignore_missing_header: Whether to continue parsing if missing header.
                                  Will assume NEM12 format.
    :returns: The file that was created
    """

    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == ".zip":
        log.debug("Extracting zip file")
        with zipfile.ZipFile(file_path, "r") as archive:
            for csv_file in archive.namelist():
                with archive.open(csv_file) as csv_text:
                    # Zip file is open in binary mode
                    # So decode then convert back to list
                    nmi_file = csv_text.read().decode("utf-8").splitlines()

                    return parse_nem_file(
                        nmi_file,
                        file_name=csv_file,
                        ignore_missing_header=ignore_missing_header,
                    )

    with open(file_path) as nmi_file:
        return parse_nem_file(nmi_file, ignore_missing_header=ignore_missing_header)


def parse_nem_file(nem_file, file_name="", ignore_missing_header=False) -> NEMFile:
    """ Parse NEM file and return meter readings named tuple """
    reader = csv.reader(nem_file, delimiter=",")
    first_row = next(reader, None)

    # Some Powercor/Citipower files have empty line at start, skip if so.
    if not first_row:
        first_row = next(reader, None)

    header = parse_header_row(
        first_row,
        ignore_missing_header=ignore_missing_header,
        file_name=getattr(nem_file, "name", file_name),
    )

    if header.assumed:
        # We have to parse the first row again so we don't miss any data.
        reader = chain([first_row], reader)
        return parse_nem12_rows(reader, header=header, file_name=nem_file)
    if header.version_header == "NEM12":
        return parse_nem12_rows(reader, header=header, file_name=nem_file)
    else:
        return parse_nem13_rows(reader, header=header, file_name=nem_file)


def parse_header_row(
    row: List[Any], ignore_missing_header=False, file_name=None
) -> HeaderRecord:
    """ Parse first row of NEM file """

    record_indicator = int(row[0])
    if record_indicator != 100:
        if ignore_missing_header:
            log.warning("Missing header (100) row, assuming NEM12.")
            header = HeaderRecord("NEM12", None, "", "", file_name, True)
        else:
            raise ValueError("NEM Files must start with a 100 row")
    else:
        header = parse_100_row(row, file_name)
        if header.version_header not in ["NEM12", "NEM13"]:
            raise ValueError("Invalid NEM version {}".format(header.version_header))

    log.debug("Parsing %s file %s ...", header.version_header, file_name)
    return header


def parse_100_row(row: List[Any], file_name: str) -> HeaderRecord:
    """ Parse header record (100) """
    return HeaderRecord(
        row[1], parse_datetime(row[2]), row[3], row[4], file_name, False
    )


def parse_nem12_rows(
    nem_list: Iterable, header: HeaderRecord, file_name=None
) -> NEMFile:
    """ Parse NEM row iterator and return meter readings named tuple """
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

    return NEMFile(header, readings, trans)


def parse_nem13_rows(
    nem_list: Iterable, header: HeaderRecord, file_name=None
) -> NEMFile:
    """ Parse NEM row iterator and return meter readings named tuple """
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
    return NEMFile(header, readings, trans)


def calculate_manual_reading(basic_data: BasicMeterData) -> Reading:
    """ Calculate the interval between two manual readings """
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
    """ Parse NMI data details record (200) """

    next_read = None  # Next scheduled read is an optional field
    if len(row) > 9:
        next_read = parse_datetime(row[9])

    return NmiDetails(
        row[1], row[2], row[3], row[4], row[5], row[6], row[7], int(row[8]), next_read
    )


def parse_250_row(row: list) -> BasicMeterData:
    """ Parse basic meter data record (250) """
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
    """ Interval data record (300) """

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
    """ Convert interval values into tuples with datetime
    """
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
    """ Convert reading value to float (if possible) """
    try:
        return float(val)
    except ValueError:
        log.warning('Reading of "%s" is not a number', val)
        return None  # Not a valid reading


def parse_400_row(row: list) -> tuple:
    """ Interval event record (400) """

    return EventRecord(int(row[1]), int(row[2]), row[3], row[4], row[5])


def update_reading_events(readings, event_record):
    """ Updates readings from a 300 row to reflect any events found in a
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
    """ Parse B2B details record """
    return B2BDetails12(row[1], row[2], row[3], row[4])


def parse_550_row(row: list) -> tuple:
    """ Parse B2B details record """
    return B2BDetails13(row[1], row[2], row[3], row[4])


def parse_datetime(record: str) -> Optional[datetime]:
    """ Parse a datetime string into a python datetime object """
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
