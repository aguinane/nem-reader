"""
    nemreader.nem_objects
    ~~~~~
    Define named tuple data classes
"""


from datetime import datetime
from typing import NamedTuple
from typing import Optional, List, Dict


class HeaderRecord(NamedTuple):
    """ Header record (100) """

    version_header: str
    creation_date: Optional[datetime]
    from_participant: str
    to_participant: str
    file_name: str
    assumed: bool


class NmiDetails(NamedTuple):
    """ NMI data details record (200)"""

    nmi: str
    nmi_configuration: str
    register_id: str
    nmi_suffix: str
    mdm_datastream_identifier: str
    meter_serial_number: str
    uom: str
    interval_length: int
    next_scheduled_read_date: Optional[datetime]


class Reading(NamedTuple):
    """ Represents a meter reading """

    t_start: datetime
    t_end: datetime
    read_value: float
    uom: str
    meter_serial_number: str
    quality_method: Optional[str]
    event_code: Optional[str]
    event_desc: Optional[str]
    read_start: Optional[datetime]
    read_end: Optional[datetime]


class BasicMeterData(NamedTuple):
    """ Basic meter data record (250) """

    nmi: str
    nmi_configuration: str
    register_id: str
    nmi_suffix: str
    mdm_data_stream_identifier: str
    meter_serial_number: str
    direction_indicator: str
    previous_register_read: str
    previous_register_read_datetime: Optional[datetime]
    previous_quality_method: str
    previous_reason_code: int
    previous_reason_description: str
    current_register_read: str
    current_register_read_datetime: Optional[datetime]
    current_quality_method: str
    current_reason_code: int
    current_reason_description: str
    quantity: float
    uom: str
    next_scheduled_read_date: Optional[datetime]
    update_datetime: Optional[datetime]
    msats_load_datetime: Optional[datetime]


class IntervalRecord(NamedTuple):
    """ Interval data record (300) """

    interval_date: Optional[datetime]
    interval_values: List[Reading]
    quality_method: str
    meter_serial_number: str
    reason_code: str
    reason_description: str
    update_datetime: Optional[datetime]
    msats_load_datatime: Optional[datetime]


class EventRecord(NamedTuple):
    """ Interval event record (400) """

    start_interval: int
    end_interval: int
    quality_method: str
    reason_code: str
    reason_description: str


class B2BDetails12(NamedTuple):
    """ B2B details record (500) """

    trans_code: str
    ret_service_order: str
    read_datetime: Optional[datetime]
    index_read: str


class B2BDetails13(NamedTuple):
    """ B2B details record (550) """

    previous_trans_code: str
    previous_ret_service_order: str
    current_trans_code: str
    current_ret_service_order: str


class NEMFile(NamedTuple):
    """ Represents a meter reading """

    header: HeaderRecord
    readings: Dict[str, Dict[str, List[Reading]]]
    transactions: Dict[str, Dict[str, list]]
