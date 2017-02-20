from collections import namedtuple

Reading = namedtuple(
    'Reading',
    ['reading_start', 'reading_end', 'reading_value', 'UOM', 'quality_method', 'event']
)


NmiDetails = namedtuple(
    'NmiDetails',
    ['nmi',
     'nmi_configuration',
     'register_id',
     'nmi_suffix',
     'mdm_datastream_identitfier',
     'meter_serial_number',
     'uom',
     'interval_length',
     'next_scheduled_read_date']
)


HeaderRecord = namedtuple(
    'HeaderRecord',
    ['version_header',
     'datetime',
     'from_participant',
     'to_participant']
)


IntervalRecord = namedtuple(
    'IntervalRecord',
    ['interval_data',
     'interval_values',
     'quality_method',
     'reason_code',
     'reason_description',
     'update_datetime',
     'MSATS_load_datatime']
)


EventRecord = namedtuple(
    'IntervalRecord',
    ['start_interval',
     'end_interval',
     'quality_method',
     'reason_code',
     'reason_description']
)


BasicMeterData = namedtuple(
    'BasicMeterData',
    ['nmi',
     'nmi_configuration',
     'register_id',
     'nmi_suffix',
     'mdm_data_stream_identifier',
     'meter_serial_number',
     'direction_indicator',
     'previous_register_read',
     'previous_register_read_datetime',
     'previous_quality_method',
     'previous_reason_code',
     'previous_reason_description',
     'current_register_read',
     'current_register_read_datetime',
     'current_quality_method',
     'current_reason_code',
     'current_reason_description',
     'quantity',
     'uom',
     'next_scheduled_read_date',
     'update_datetime',
     'msats_load_datetime']
)

NEMFile = namedtuple(
    'NEMFile', ['header', 'readings']
)