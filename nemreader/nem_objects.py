"""
    nemreader.nem_objects
    ~~~~~
    Define named tuple data classes
"""

from collections import namedtuple
from datetime import datetime
from typing import NamedTuple, Optional, Any


class NEMFile(NamedTuple):
    """ Represents a meter reading """
    header: Any
    readings: Any
    transactions: Any


class Reading(NamedTuple):
    """ Represents a meter reading """
    t_start: datetime
    t_end: datetime
    read_value: float
    uom: str
    quality_method: Optional[str]
    event_code: Optional[str]
    event_desc: Optional[str]
    read_start: Optional[datetime]
    read_end: Optional[datetime]


class NmiDetails(NamedTuple):
    """ Represents meter metadata """
    nmi: str
    nmi_configuration: str
    register_id: str
    nmi_suffix: str
    mdm_datastream_identifier: str
    meter_serial_number: str
    uom: str
    interval_length: int
    next_scheduled_read_date: datetime


HeaderRecord = namedtuple('HeaderRecord', [
    'version_header',
    'datetime',
    'from_participant',
    'to_participant',
    'file_name',
])

IntervalRecord = namedtuple('IntervalRecord', [
    'interval_data', 'interval_values', 'quality_method', 'reason_code',
    'reason_description', 'update_datetime', 'msats_load_datatime'
])

EventRecord = namedtuple('IntervalRecord', [
    'start_interval', 'end_interval', 'quality_method', 'reason_code',
    'reason_description'
])

BasicMeterData = namedtuple('BasicMeterData', [
    'nmi', 'nmi_configuration', 'register_id', 'nmi_suffix',
    'mdm_data_stream_identifier', 'meter_serial_number', 'direction_indicator',
    'previous_register_read', 'previous_register_read_datetime',
    'previous_quality_method', 'previous_reason_code',
    'previous_reason_description', 'current_register_read',
    'current_register_read_datetime', 'current_quality_method',
    'current_reason_code', 'current_reason_description', 'quantity', 'uom',
    'next_scheduled_read_date', 'update_datetime', 'msats_load_datetime'
])

B2BDetails12 = namedtuple(
    'B2BDetails12',
    ['trans_code', 'ret_service_order', 'read_datetime', 'index_read'])

B2BDetails13 = namedtuple('B2BDetails13', [
    'previous_trans_code', 'previous_ret_service_order', 'current_trans_code',
    'current_ret_service_order'
])
