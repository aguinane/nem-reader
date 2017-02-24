from collections import namedtuple

Reading = namedtuple(
    'Reading',
    ['t_start', 't_end',
     'read_value',
     'uom', 'quality_method', 'event',
     'read_start', 'read_end']
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

B2BDetails12 = namedtuple(
    'B2BDetails12',
    ['trans_code',
     'ret_service_order',
     'read_datetime',
     'index_read']

)

B2BDetails13 = namedtuple(
    'B2BDetails13',
    ['previous_trans_code',
     'previous_ret_service_order',
     'current_trans_code',
     'current_ret_service_order']
)

NEMFile = namedtuple(
    'NEMFile', ['header', 'readings', 'transactions']
)