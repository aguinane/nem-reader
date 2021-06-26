from typing import Iterable, Generator
from datetime import timedelta
from .nem_objects import Reading


def split_multiday_reads(
    readings: Iterable[Reading],
) -> Generator[Reading, None, None]:
    """ Split readings into daily intervals if they exceed 24 hours """
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
    """ Split a single reading into even daily readings """
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
