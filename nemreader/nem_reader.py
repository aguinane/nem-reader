import csv
import logging
import datetime
from collections import namedtuple


Reading = namedtuple(
    'Reading',
    ['reading_start', 'reading_end', 'reading_value', 'UOM']
)


class MeterRecord(object):
    """ A NEM meter record
    """

    def __init__(self, file_path):
        """ Initialise Object
        """
        self.file_path = file_path
        self.readings = dict()

        with open(file_path) as nem_file:
            reader = csv.reader(nem_file, delimiter=',', quotechar='"')
            for i, row in enumerate(reader):
                if i == 0:
                    if row[0] != '100':
                        logging.warning('NEM Files must start with a 100 row')

                    HeaderRecord = parse_100_row(row)
                    self.version_header = HeaderRecord.VersionHeader
                    self.file_created = HeaderRecord.DateTime
                    self.file_created_by = HeaderRecord.FromParticipant
                    self.file_created_for = HeaderRecord.ToParticipant
                    continue

                record_indicator = int(row[0])
                if record_indicator == 900:
                    break  # End of file

                if self.version_header == 'NEM12':
                    if record_indicator == 200:
                        MeterData = parse_200_row(row)
                        self.NMI = MeterData.NMI
                        self.NMI_configuration = MeterData.NMIConfiguration
                        uom = MeterData.UOM
                        interval = MeterData.IntervalLength
                        nmi_suffix = MeterData.NMISuffix
                        if nmi_suffix not in self.readings:
                            self.readings[nmi_suffix] = []

                    if record_indicator == 300:
                        IntervalRecord = parse_300_row(row, interval, uom)
                        for reading in IntervalRecord.IntervalValues:
                            self.readings[nmi_suffix].append(reading)

                elif self.version_header == 'NEM13':
                    BasicMeterData = parse_250_row(row)
                    self.NMI = BasicMeterData.NMI
                    self.NMI_configuration = BasicMeterData.NMIConfiguration
                    nmi_suffix = BasicMeterData.NMISuffix
                    if nmi_suffix not in self.readings:
                        self.readings[nmi_suffix] = []
                    reading = calculate_manual_reading(BasicMeterData)
                    self.readings[nmi_suffix].append(reading)

                else:
                    msg = "The NEM version {} is invalid".format(
                        self.version_header)
                    logging.warning(msg)


def calculate_manual_reading(BasicMeterData):
    """ Calculate the interval between two manual readings
    """
    reading_start = BasicMeterData.PreviousRegisterReadDateTime
    reading_end = BasicMeterData.CurrentRegisterReadDateTime
    value = BasicMeterData.CurrentRegisterRead - BasicMeterData.PreviousRegisterRead
    uom = BasicMeterData.UOM
    return Reading(reading_start, reading_end, value, uom)


def parse_100_row(row):
    """ Parse header record (100)
    """
    HeaderRecord = namedtuple(
        'HeaderRecord',
        ['VersionHeader',
         'DateTime',
         'FromParticipant',
         'ToParticipant']
    )
    return HeaderRecord(row[1],
                        parse_datetime(row[2], '%Y%m%d%H%M'),
                        row[3],
                        row[4])


def parse_200_row(row):
    """ Parse NMI data details record (200)
    """

    MeterData = namedtuple(
        'MeterData',
        ['NMI',
         'NMIConfiguration',
         'RegisterID',
         'NMISuffix',
         'MDMDataStreamIdentifier',
         'MeterSerialNumber',
         'UOM',
         'IntervalLength',
         'NextScheduledReadDate'
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
    interval_date = parse_datetime(row[1], '%Y%m%d')
    last_interval = 1 + num_intervals
    interval_values = parse_intervals(
        row[2:last_interval], interval_date, interval, uom)

    IntervalRecord = namedtuple(
        'IntervalRecord',
        [
            'IntervalDate',
            'IntervalValues',
            'QualityMethod',
            'ReasonCode',
            'ReasonDescription',
            'UpdateDateTime',
            'MSATSLoadDateTime'
        ]
    )

    return IntervalRecord(interval_date,
                          interval_values,
                          row[last_interval + 1],
                          row[last_interval + 2],
                          row[last_interval + 3],
                          parse_datetime(row[last_interval + 4]),
                          parse_datetime(row[last_interval + 5]),
                          )


def parse_400_row(row):
    """ Interval event record (400)
    """

    EventRecord = namedtuple(
        'IntervalRecord',
        [
            'StartInterval',
            'EndInterval',
            'QualityMethod',
            'ReasonCode',
            'ReasonDescription'
        ]
    )

    return EventRecord(int(row[1]),
                       int(row[2]),
                       row[3],
                       row[4],
                       row[5]
                       )


def parse_intervals(rows, interval_date, interval, uom):
    """ Convert interval values into tuples with datetime
    """

    interval_delta = datetime.timedelta(minutes=interval)
    for i, row in enumerate(rows):
        reading_start = interval_date + (i * interval_delta) - interval_delta
        reading_end = interval_date + (i * interval_delta)
        yield Reading(reading_start, reading_end, float(row), uom)


def parse_datetime(record, date_format='%Y%m%d%H%M%S'):
    """ Parse a datetime string into a python datetime object """
    if record == '':
        return None
    else:
        return datetime.datetime.strptime(record, date_format)
