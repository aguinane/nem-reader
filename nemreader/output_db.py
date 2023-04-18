import logging
import os
from pathlib import Path
from typing import Optional

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
