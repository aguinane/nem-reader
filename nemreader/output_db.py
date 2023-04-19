import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

from dateutil.parser import isoparse
from sqlite_utils import Database

from .nem_reader import NEMFile
from .split_days import make_set_interval, split_multiday_reads

log = logging.getLogger(__name__)


def output_as_sqlite(
    file_name: Path,
    output_dir: str = ".",
    output_file: str = "nemdata.db",
    split_days: bool = False,
    set_interval: Optional[int] = None,
    replace: bool = False,
) -> Path:
    """Export all channels to sqlite file"""

    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_path = output_dir / output_file
    if replace and output_path.exists():
        os.remove(output_path)  # Clear existing database file

    db = Database(output_path)

    nf = NEMFile(file_name, strict=False)
    m = nf.nem_data()
    nmis = m.readings.keys()
    for nmi in nmis:
        channels = list(m.transactions[nmi].keys())
        nmi_readings = m.readings[nmi]

        for ch in channels:
            if split_days or set_interval:
                nmi_readings[ch] = list(split_multiday_reads(nmi_readings[ch]))

            if set_interval:
                nmi_readings[ch] = list(
                    make_set_interval(nmi_readings[ch], set_interval)
                )

            items = []
            for x in nmi_readings[ch]:
                item = {
                    "nmi": nmi,
                    "channel": ch,
                    "t_start": x.t_start,
                    "t_end": x.t_end,
                    "value": x.read_value,
                    "quality_method": x.quality_method,
                    "event_code": x.event_code,
                    "event_desc": x.event_desc,
                }
                items.append(item)
            db["readings"].upsert_all(
                items,
                pk=("nmi", "channel", "t_start"),
                column_order=("nmi", "channel", "t_start"),
            )

    db.create_view(
        "nmi_summary",
        """
        SELECT nmi, channel, MIN(t_start) as first_interval, MAX(t_end) as last_interval
        FROM readings
        GROUP BY nmi, channel
    """,
        replace=True,
    )
    return output_path


def time_of_day(start: datetime) -> str:
    """Get time of day period"""
    s = start
    if s.hour < 4:
        return "Night"
    if s.hour < 9:
        return "Morning"
    if s.hour < 16:
        return "Day"
    if s.hour < 21:
        return "Evening"
    return "Night"


def get_nmis(db_path: Path) -> List[str]:
    nmis = []
    db = Database(db_path)
    for row in db.query("select distinct nmi from nmi_summary"):
        nmis.append(row["nmi"])
    return nmis


def get_nmi_channels(db_path: Path, nmi: str) -> List[str]:
    channels = []
    db = Database(db_path)
    for row in db.query("select * from nmi_summary where nmi = :nmi", {"nmi": nmi}):
        channels.append(row["channel"])
    return channels


def get_nmi_date_range(db_path: Path, nmi: str) -> Tuple[datetime, datetime]:
    db = Database(db_path)
    sql = """select MIN(first_interval) start, MAX(last_interval) end 
            from nmi_summary where nmi = :nmi
            """
    rows = list(db.query(sql, {"nmi": nmi}))
    row = rows[0]
    start = isoparse(row["start"])
    end = isoparse(row["end"])
    return start, end


class EnergyReading(NamedTuple):
    start: datetime
    value: float


def get_nmi_readings(db_path: Path, nmi: str, channel: str) -> List[EnergyReading]:
    reads = []
    db = Database(db_path)
    for r in db.query(
        "select * from readings where nmi = :nmi and channel = :ch",
        {"nmi": nmi, "ch": channel},
    ):
        start = isoparse(r["t_start"])
        value = float(r["value"])
        read = EnergyReading(start=start, value=value)
        reads.append(read)
    return reads


def calc_nmi_daily_summary(db_path: Path, nmi: str):
    channels = get_nmi_channels(db_path, nmi)

    imp_values = defaultdict(lambda: defaultdict(int))
    exp_values = defaultdict(int)
    for ch in channels:
        if ch[0] not in ["B", "E"]:
            continue  # Skip other channels
        feed_in = True if ch[0] == "B" else False
        for read in get_nmi_readings(db_path, nmi, ch):
            day = read.start.strftime("%Y-%m-%d")
            if feed_in:
                exp_values[day] += read.value
            else:
                tod = time_of_day(read.start)
                imp_values[day][tod] += read.value

    for day in imp_values.keys():
        imp1 = round(imp_values[day]["Morning"], 3)
        imp2 = round(imp_values[day]["Day"], 3)
        imp3 = round(imp_values[day]["Evening"], 3)
        imp4 = round(imp_values[day]["Night"], 3)
        imp = imp1 + imp2 + imp3 + imp4
        exp = round(exp_values[day], 3)
        item = {
            "nmi": nmi,
            "day": day,
            "imp": imp,
            "exp": exp,
            "imp_morning": imp1,
            "imp_day": imp2,
            "imp_evening": imp3,
            "imp_night": imp4,
        }
        yield item


def extend_sqlite(db_path: Path) -> None:
    """Add summary tables to SQLite DB export"""
    db = Database(db_path)
    nmis = get_nmis(db_path)
    for nmi in nmis:
        items = calc_nmi_daily_summary(db_path, nmi)
        db["daily_reads"].upsert_all(
            items, pk=("nmi", "day"), column_order=("nmi", "day")
        )
    logging.info("Updated day data")

    db.create_view(
        "monthly_reads",
        """
    SELECT nmi, substr(day,1,7) as month,
    count(day) as num_days, sum(imp) as imp, sum(exp) as exp,
    sum(imp_morning) as imp_morning, sum(imp_day) as imp_day,
    sum(imp_evening) as imp_evening, sum(imp_night) as imp_night
    FROM daily_reads
    GROUP BY nmi, substr(day,1,7)
    ORDER BY 1, 2
    """,
        replace=True,
    )
    logging.info("Created monthly view")
