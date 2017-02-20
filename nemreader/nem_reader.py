import csv
import logging
import datetime
import nemreader.nem_objects as nm


def flatten_list(l):
    """ takes a list of lists, l and returns a flat list
    """
    return [v for inner_l in l for v in inner_l]


def read_nem_file(file_path):
    with open(file_path) as nmi_file:
        return parse_nem_file(nmi_file)


def parse_nem_file(nem_file):
    reader = csv.reader(nem_file, delimiter=',', quotechar='"')
    
    header = None # metadata from header row
    readings = {} # readings nested by NMI then channel
    nmi_d = None # current NMI details block that readings apply to

    for i, row in enumerate(reader):
        record_indicator = int(row[0])

        if i == 0 and record_indicator != 100:
            raise ValueError("NEM Files must start with a 100 row")

        if record_indicator == 100:
            header = parse_100_row(row)
            if header.version_header not in ['NEM12', 'NEM13']:
                raise ValueError(
                    "Invalid NEM version {}".format(header.version_header)
                )

        elif record_indicator == 900:
            for nmi in readings:
                for suffix in readings[nmi]:
                    readings[nmi][suffix] = flatten_list(readings[nmi][suffix])
            break  # End of file

        elif header.version_header == 'NEM12' and record_indicator == 200:
            try:
                nmi_details = parse_200_row(row)
            except ValueError:
                logging.error('Error passing 200 row:')
                logging.error(row)
                raise
            nmi_d = nmi_details

            if nmi_d.nmi not in readings:
                readings[nmi_d.nmi] = {}
            if nmi_d.nmi_suffix not in readings[nmi_d.nmi]:
                readings[nmi_d.nmi][nmi_d.nmi_suffix] = []

        elif header.version_header == 'NEM12' and record_indicator == 300:
            interval_record = parse_300_row(row, nmi_d.interval_length, nmi_d.uom)
            # don't flatten the list of interval readings at this stage,
            # as they may need to be adjusted by a 400 row
            readings[nmi_d.nmi][nmi_d.nmi_suffix].append(
                interval_record.interval_values
            )

        elif header.version_header == 'NEM12' and record_indicator == 400:
            event_record = parse_400_row(row)
            readings[nmi_d.nmi][nmi_d.nmi_suffix][-1] = update_readings(
                readings[nmi_d.nmi][nmi_d.nmi_suffix][-1], event_record
            )

        elif header.version_header == 'NEM13' and record_indicator == 250:
            # Reset the blocking for current 200 row.
            # According to the MDFF spec a  200 and 250 row shouldn't
            # be in the same file.
            nmi_d = None
            basic_data = parse_250_row(row)
            reading = calculate_manual_reading(basic_data)

            if basic_data.nmi not in readings:
                readings[basic_data.nmi] = {}
            if basic_data.nmi_suffix not in readings[basic_data.nmi]:
                readings[basic_data.nmi][basic_data.nmi_suffix] = []

            readings[basic_data.nmi][basic_data.nmi_suffix].append(
                [reading]
            )


        else:
            logging.warning(
                "Record indicator {} not supported and was skipped".format(record_indicator)
            )
    return nm.NEMFile(header, readings)


def calculate_manual_reading(basic_data):
    """ Calculate the interval between two manual readings
    """
    reading_start = basic_data.previous_register_read_datetime
    reading_end = basic_data.current_register_read_datetime
    value = basic_data.current_register_read - basic_data.previous_register_read
    uom = basic_data.uom
    quality_method = basic_data.current_quality_method
    return nm.Reading(reading_start, reading_end, value, uom, quality_method, "")


def parse_100_row(row):
    """ Parse header record (100)
    """

    return nm.HeaderRecord(row[1],
                           parse_datetime(row[2]),
                           row[3],
                           row[4])


def parse_200_row(row):
    """ Parse NMI data details record (200)
    """

    return nm.NmiDetails(row[1],
                         row[2],
                         row[3],
                         row[4],
                         row[5],
                         row[6],
                         row[7],
                         int(row[8]),
                         parse_datetime(row[9]))


def parse_250_row(row):
    """ Parse basic meter data record (250)
    """
    return nm.BasicMeterData(row[1],
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
                             parse_datetime(row[22]))


def parse_300_row(row, interval=30, uom='kWh'):
    """ Interval data record (300)
    """

    num_intervals = int(24 / (interval / 60))
    interval_date = parse_datetime(row[1])
    last_interval = 2 + num_intervals
    quality_method = row[last_interval]

    interval_values = parse_interval_records(
        row[2:last_interval], interval_date, interval, uom, quality_method
    )

    return nm.IntervalRecord(interval_date,
                             interval_values,
                             row[last_interval + 0],
                             row[last_interval + 1],
                             row[last_interval + 2],
                             parse_datetime(row[last_interval + 3]),
                             parse_datetime(row[last_interval + 4]))


def parse_interval_records(interval_record, interval_date, interval,
                           uom, quality_method):
    """ Convert interval values into tuples with datetime
    """

    interval_delta = datetime.timedelta(minutes=interval)
    return [nm.Reading(interval_date + (i * interval_delta),
                       interval_date + (i * interval_delta) + interval_delta,
                       float(val),
                       uom,
                       quality_method,
                       "") # event is unknown at time of reading
            for i, val in enumerate(interval_record)]


def parse_400_row(row):
    """ Interval event record (400)
    """

    return nm.EventRecord(int(row[1]),
                          int(row[2]), 
                          row[3], 
                          row[4], 
                          row[5]) 


def set_reading_event(reading, event_record):
    return nm.Reading(reading.reading_start,
                      reading.reading_end,
                      reading.reading_value,
                      reading.UOM,
                      event_record.quality_method,
                      event_record.reason_description)


def update_readings(readings, event_record):
    """ updates readings from a 300 row to reflect any events found in a
        subsequent 400 row
    """
    # event intervals are 1-indexed
    for i in range(event_record.start_interval - 1, event_record.end_interval):
        readings[i] = set_reading_event(readings[i], event_record)
    return readings


def parse_datetime(record):
    """ Parse a datetime string into a python datetime object """
    if record == '':
        return None
    else:
        try:
            return datetime.datetime.strptime(record.strip(), '%Y%m%d%H%M%S')
        except ValueError:
            return datetime.datetime.strptime(record.strip(), '%Y%m%d')
