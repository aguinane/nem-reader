from datetime import datetime, timedelta
from statistics import mean
from typing import Generator, Iterable, Tuple

from .nem_objects import Reading


def split_multiday_reads(
    readings: Iterable[Reading],
) -> Generator[Reading, None, None]:
    """Split readings into daily intervals if they exceed 24 hours"""
    for r in readings:
        interval_s = int((r.t_end - r.t_start).total_seconds())
        interval_days = interval_s / 60 / 60 / 24
        if interval_days <= 1.0:
            # Don't need to do anything
            yield r
        else:
            for start, end, val in split_reading_into_days(
                r.t_start, r.t_end, r.read_value
            ):
                yield Reading(
                    start,
                    end,
                    val,
                    r.uom,
                    r.meter_serial_number,
                    r.quality_method,
                    r.event_code,
                    r.event_desc,
                    None,
                    None,
                )


def split_reading_into_days(start, end, val):
    """Split a single reading into even daily readings"""
    total_secs = (end - start).total_seconds()
    # Split first day into single day
    next_day = start.replace(hour=0, minute=0, second=0) + timedelta(days=1)
    fd_secs = (next_day - start).total_seconds()
    fd_val = val * (fd_secs / total_secs)
    yield start, next_day, fd_val

    # Generate the rest of the days
    period_start = next_day
    period_end = period_start + timedelta(days=1)
    if period_end >= end:
        period_end = end
    while period_start < end:
        if period_end > end:
            period_end = end
        period_secs = (period_end - period_start).total_seconds()
        period_val = val * (period_secs / total_secs)
        yield period_start, period_end, period_val,
        period_start += timedelta(days=1)
        period_end += timedelta(days=1)


def new_intervals(
    start_date: datetime, end_date: datetime, interval: float = 5
) -> Generator[Tuple[datetime, datetime], None, None]:
    """Generate equally spaced intervals between two dates"""
    delta = timedelta(seconds=interval * 60)
    orig_delta = end_date - start_date
    if (orig_delta / delta) % 1 != 0:
        raise ValueError(f"New interval of {delta} not an increment of {orig_delta}")
    num_intervals = int(orig_delta / delta)
    for i in range(0, num_intervals):
        start = start_date + i * delta
        end = start + delta
        yield start, end


def get_group_end(end_date: datetime, interval: int = 30) -> datetime:
    """Get interval group end time"""
    group_end = end_date
    while group_end.minute % interval != 0:
        group_end += timedelta(minutes=1)
    return group_end


def make_set_interval(
    readings: Iterable[Reading], new_interval: int = 5
) -> Iterable[Reading]:
    """Generate equally spaced values at 5-min intervals"""
    delta = timedelta(seconds=new_interval * 60)
    group_records = {}
    for r in readings:
        interval = r.t_end - r.t_start
        if interval == delta:  # No change required
            yield r
            continue

        if interval > delta:  # Need to split up smaller
            intervals = list(new_intervals(r.t_start, r.t_end, interval=new_interval))
            if r.uom and r.uom[-1].lower() == "h":
                split_val = r.read_value / len(intervals)
            else:
                split_val = r.read_value  # Average so assume flat

            for start, end in intervals:
                yield Reading(
                    start,
                    end,
                    split_val,
                    r.uom,
                    r.meter_serial_number,
                    r.quality_method,
                    r.event_code,
                    r.event_desc,
                    None,
                    None,
                )

        if interval < delta:  # Need to aggregate to bigger intervals
            # Increment dictionary value
            group_end = get_group_end(r.t_end, new_interval)
            if group_end not in group_records:
                group_records[group_end] = [r]
            else:
                group_records[group_end].append(r)

    # Output any aggregated grouped values
    for group_end in sorted(group_records.keys()):
        start = group_end - delta
        grp_readings = group_records[group_end]
        uom = grp_readings[0].uom
        meter_serial_number = grp_readings[0].meter_serial_number
        quality_methods = list(set([x.quality_method for x in grp_readings]))
        event_codes = list(set([x.event_code for x in grp_readings if x.event_code]))
        event_descs = list(set([x.event_desc for x in grp_readings if x.event_desc]))
        if len(quality_methods) == 1:
            quality_method = grp_readings[0].quality_method
            event_code = event_codes[0] if event_codes else ""
            event_desc = event_descs[0] if event_descs else ""
        else:
            quality_method = "V"
            event_code = grp_readings[0].event_code
            event_desc = grp_readings[0].event_desc

        if r.uom and r.uom[-1].lower() == "h":
            grp_value = sum([x.read_value for x in grp_readings])
        else:
            grp_value = mean([x.read_value for x in grp_readings])

        yield Reading(
            start,
            group_end,
            grp_value,
            uom,
            meter_serial_number,
            quality_method,
            event_code,
            event_desc,
            None,
            None,
        )
