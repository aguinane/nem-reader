import csv
import logging
import datetime
from collections import namedtuple


def flatten_list(l):
    """ takes a list of lists, l and returns a flat list
    """
    return [v for inner_l in l for v in inner_l]


Reading = namedtuple(
    'Reading',
    ['reading_start', 'reading_end', 'reading_value', 'UOM', 'quality_method', 'event']
)


class MeterRecord(object):
    """ A NEM meter record
    """

    def __init__(self, file_path, read_on_open=True):
        """ Initialise Object
        """
        self.readings = dict()
        self.NMI = None
        self.file_path = None

        if read_on_open:
            self.read_file(file_path)


    def read_file(self, file_path):
        self.file_path = file_path

        with open(file_path) as nem_file:
            return self.parse_file(nem_file)

    def parse_file(self, nem_file):
        reader = csv.reader(nem_file, delimiter=',', quotechar='"')
        nmi_suffix = None

        for i, row in enumerate(reader):
            record_indicator = int(row[0])

            if i == 0 and record_indicator != 100:
                raise ValueError("NEM Files must start with a 100 row")

            if record_indicator == 100:
                header_record = parse_100_row(row)
                if header_record.version_header not in ['NEM12', 'NEM13']:
                    raise ValueError(
                        "Invalid NEM version {}".format(header_record.version_header)
                    )
                self.version_header = header_record.version_header
                self.file_created = header_record.datetime
                self.file_created_by = header_record.from_participant
                self.file_created_for = header_record.to_participant

            elif record_indicator == 900:
                for nmi_suffix in self.readings:
                    self.readings[nmi_suffix] = flatten_list(self.readings[nmi_suffix])
                break  # End of file

            elif self.version_header == 'NEM12' and record_indicator == 200:
                try:
                    meter_data = parse_200_row(row)
                except ValueError:
                    logging.error('Error passing 200 row:')
                    logging.error(row)
                    raise

                if self.NMI is None:
                    self.NMI = meter_data.NMI
                elif self.NMI != meter_data.NMI:
                    msg = "Different NMIs in same file: {}, {}".format(
                        self.NMI, meter_data.NMI
                    )
                    raise ValueError(msg)

                self.NMI_configuration = meter_data.NMI_configuration
                uom = meter_data.UOM
                interval = meter_data.interval_length
                nmi_suffix = meter_data.NMI_suffix
                if nmi_suffix not in self.readings:
                    self.readings[nmi_suffix] = []

            elif self.version_header == 'NEM12' and record_indicator == 300:
                interval_record = parse_300_row(row, interval, uom)
                # don't flatten the list of interval readings at this stage,
                # as they may need to be adjusted by a 400 row
                self.readings[nmi_suffix].append(interval_record.interval_values)

            elif self.version_header == 'NEM12' and record_indicator == 400:
                event_record = parse_400_row(row)
                self.readings[nmi_suffix][-1] = update_readings(
                    self.readings[nmi_suffix][-1], event_record
                )

            elif self.version_header == 'NEM13' and record_indicator == 250:
                BasicMeterData = parse_250_row(row)
                self.NMI = BasicMeterData.NMI
                self.NMI_configuration = BasicMeterData.NMIConfiguration
                nmi_suffix = BasicMeterData.NMISuffix
                if nmi_suffix not in self.readings:
                    self.readings[nmi_suffix] = []
                reading = calculate_manual_reading(BasicMeterData)
                self.readings[nmi_suffix].append([reading])

            else:
                logging.warning(
                    "Record indicator {} not supported and was skipped".format(record_indicator)
                )


def calculate_manual_reading(basic_meter_data):
    """ Calculate the interval between two manual readings
    """
    reading_start = basic_meter_data.PreviousRegisterReadDateTime
    reading_end = basic_meter_data.CurrentRegisterReadDateTime
    value = basic_meter_data.CurrentRegisterRead - basic_meter_data.PreviousRegisterRead
    uom = basic_meter_data.UOM
    quality_method = basic_meter_data.CurrentQualityMethod
    return Reading(reading_start, reading_end, value, uom, quality_method, "")


def parse_100_row(row):
    """ Parse header record (100)
    """
    HeaderRecord = namedtuple(
        'HeaderRecord',
        ['version_header',
         'datetime',
         'from_participant',
         'to_participant']
    )
    return HeaderRecord(row[1],
                        parse_datetime(row[2]),
                        row[3],
                        row[4])


def parse_200_row(row):
    """ Parse NMI data details record (200)
    """

    MeterData = namedtuple(
        'MeterData',
        ['NMI',
         'NMI_configuration',
         'register_id',
         'NMI_suffix',
         'MDM_datastream_identitfier',
         'meter_serial_number',
         'UOM',
         'interval_length',
         'next_scheduled_read_date'
         ]
    )

    return MeterData(row[1],
                     row[2],
                     row[3],
                     row[4],
                     row[5],
                     row[6],
                     row[7],
                     int(row[8]),
                     parse_datetime(row[9])
                     )


def parse_250_row(row):
    """ Parse basic meter data record (250)
    """

    BasicMeterData = namedtuple(
        'BasicMeterData',
        ['NMI',
         'NMIConfiguration',
         'RegisterID',
         'NMISuffix',
         'MDMDataStreamIdentifier',
         'MeterSerialNumber',
         'DirectionIndicator',
         'PreviousRegisterRead',
         'PreviousRegisterReadDateTime',
         'PreviousQualityMethod',
         'PreviousReasonCode',
         'PreviousReasonDescription',
         'CurrentRegisterRead',
         'CurrentRegisterReadDateTime',
         'CurrentQualityMethod',
         'CurrentReasonCode',
         'CurrentReasonDescription',
         'Quantity',
         'UOM',
         'NextScheduledReadDate',
         'UpdateDateTime',
         'MSATSLoadDateTime'
         ]
    )

    return BasicMeterData(row[1],
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
                          parse_datetime(row[22])
                          )


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

    IntervalRecord = namedtuple(
        'IntervalRecord',
        [
            'interval_data',
            'interval_values',
            'quality_method',
            'reason_code',
            'reason_description',
            'update_datetime',
            'MSATS_load_datatime'
        ]
    )

    return IntervalRecord(interval_date,
                          interval_values,
                          row[last_interval + 0],
                          row[last_interval + 1],
                          row[last_interval + 2],
                          parse_datetime(row[last_interval + 3]),
                          parse_datetime(row[last_interval + 4]),
                          )


def parse_interval_records(interval_record, interval_date, interval,
                           uom, quality_method):
    """ Convert interval values into tuples with datetime
    """

    interval_delta = datetime.timedelta(minutes=interval)
    return [Reading(interval_date + (i * interval_delta),
                    interval_date + (i * interval_delta) + interval_delta,
                    float(val),
                    uom,
                    quality_method,
                    "") # event is unknown at time of reading
            for i, val in enumerate(interval_record)]


def parse_400_row(row):
    """ Interval event record (400)
    """

    EventRecord = namedtuple(
        'IntervalRecord',
        [
            'start_interval',
            'end_interval',
            'quality_method',
            'reason_code',
            'reason_description'
        ]
    )

    return EventRecord(int(row[1]),
                       int(row[2]),
                       row[3],
                       row[4],
                       row[5]
                       )


def set_reading_event(reading, event_record):
    return Reading(reading.reading_start,
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
