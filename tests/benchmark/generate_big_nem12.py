#!/usr/bin/env python3
"""Generate a large, synthetic NEM12 file for benchmarking the parser.

The defaults give one NMI with 20 channels over two clean, non-leap years
(730 days) of 5-minute interval data, with a mix of A and V quality days and
the 400 event records that a V day requires. That comes to roughly 4.2
million readings in a file of about 30 MB.

Usage:
    uv run python scripts/generate_big_nem12.py                # write to stdout
    uv run python scripts/generate_big_nem12.py --days 30 > small.nem12.csv
    uv run python scripts/generate_big_nem12.py --seed 7 > seed7.nem12.csv

"""

from __future__ import annotations

import argparse
import itertools
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import IO

LINE_TERMINATOR = b"\r"

FAMILIES = ("B", "E", "K", "Q")
CHANNEL_NUMBERS = ("1", "2", "3", "4", "5", "6", "7")

UOM_BY_FAMILY = {"B": "KWH", "E": "KWH", "K": "KVARH", "Q": "KVARH"}

# Reason codes weights seen on 400 segments.
REASON_CODE_WEIGHTS = (("", 70), ("89", 10), ("87", 10), ("79", 10))

# Quality methods on 400 segments.
EVENT_QUALITY_WEIGHTS = (("A", 99), ("F17", 1))


@dataclass
class Config:
    """Everything that shapes the generated file."""

    seed: int = 12345
    start_date: date = date(2021, 1, 1)
    days: int = (date(2023, 1, 1) - start_date).days # 730
    n_channels: int = 20
    interval: int = 5  # minutes
    nmi: str = "SYNTH00001"
    serial_base: int = 1000000
    # V days per channel (quality varies across the day, so 400 records follow).
    # An uneven spread across channels, scaled if a different day count is asked
    # for. The pattern cycles when there are more channels than entries.
    v_day_pattern: tuple[int, ...] = tuple([7] * 12 + [11] * 12 + [13] * 4)
    v_day_pattern_days: int = 730
    segments_per_v_day: int = 3
    channels: tuple[tuple[str, str], ...] = ()

    def v_days_for_channel(self, ch_index: int) -> int:
        """How many V days this channel gets, scaled to the day count."""
        base = self.v_day_pattern[ch_index % len(self.v_day_pattern)]
        scaled = round(base * self.days / self.v_day_pattern_days)
        return min(scaled, self.days)

    def __post_init__(self) -> None:
        if not self.channels:
            # (suffix, uom) in number-major order, truncated to n_channels.
            ordered = [
                (f"{fam}{num}", UOM_BY_FAMILY[fam])
                for num in CHANNEL_NUMBERS
                for fam in FAMILIES
            ]
            if self.n_channels > len(ordered):
                raise ValueError(
                    f"n_channels {self.n_channels} exceeds the "
                    f"{len(ordered)} channels the number pool allows"
                )
            self.channels = tuple(ordered[: self.n_channels])

    @property
    def intervals_per_day(self) -> int:
        return 1440 // self.interval

    @property
    def nmi_configuration(self) -> str:
        # Family-grouped list of the channels in use, e.g. B1B2...E1E2...Q5.
        suffixes = {suffix for suffix, _ in self.channels}
        return "".join(
            f"{fam}{num}"
            for fam in FAMILIES
            for num in CHANNEL_NUMBERS
            if f"{fam}{num}" in suffixes
        )


def weighted_choice(rng: random.Random, weighted: tuple[tuple[str, int], ...]) -> str:
    """Pick one value from (value, weight) pairs."""
    values, weights = zip(*weighted, strict=True)
    return rng.choices(values, weights=weights, k=1)[0]


def daily_profile(rng: random.Random, intervals: int, uom: str) -> list[float]:
    """Build one day of plausible interval readings.

    A smooth daily shape (a morning and evening rise) plus noise, kept
    non-negative. Reactive channels (KVARH) are scaled down. The numbers are
    invented and carry no real load; they only give the parser realistic
    4-decimal values to chew through.
    """
    scale = 0.4 if uom == "KVARH" else 1.0
    phase = rng.uniform(0, 2 * math.pi)
    base = rng.uniform(0.2, 0.8)
    values = []
    for i in range(intervals):
        hour = i * 24 / intervals
        # Two humps across the day.
        shape = math.sin((hour / 24) * 2 * math.pi + phase) + 0.5 * math.sin(
            (hour / 24) * 4 * math.pi
        )
        val = base + scale * (0.6 + 0.4 * shape) + rng.gauss(0, 0.05)
        values.append(max(0.0, val))
    return values


def make_400_segments(
    rng: random.Random, intervals: int, segments: int
) -> list[tuple[int, int, str, str]]:
    cuts = sorted(rng.sample(range(1, intervals), k=segments - 1))
    bounds = [0, *cuts, intervals]
    rows = []
    for lo, hi in itertools.pairwise(bounds):
        quality = weighted_choice(rng, EVENT_QUALITY_WEIGHTS)
        reason = weighted_choice(rng, REASON_CODE_WEIGHTS)
        rows.append((lo + 1, hi, quality, reason))
    return rows


def format_values(values: list[float]) -> str:
    """Format readings as 4-decimal fields."""
    return ",".join(f"{v:.4f}" for v in values)

def generate(cfg: Config, fh: IO[bytes]) -> tuple[dict[str, int], int]:
    """Write the file and return a small summary of what was produced."""
    rng = random.Random(cfg.seed)
    intervals = cfg.intervals_per_day
    delta_day = timedelta(days=1)

    counts = {"200": 0, "300": 0, "400": 0}
    bytes_written = 0

    def write(fields: list[str]) -> None:
        nonlocal bytes_written
        bytes_written += fh.write(",".join(fields).encode())
        bytes_written += fh.write(LINE_TERMINATOR)

    for ch_index, (suffix, uom) in enumerate(cfg.channels):
        serial = str(cfg.serial_base + ch_index)

        # 200 record
        write(
            [
                "200",
                cfg.nmi,
                cfg.nmi_configuration,
                suffix,  # RegisterID mirrors the suffix
                suffix,
                "",
                serial,
                uom,
                str(cfg.interval),
                "",
            ]
        )
        counts["200"] += 1

        # Decide which days vary in quality (get 400 records).
        n_v_days = cfg.v_days_for_channel(ch_index)
        v_days = set(rng.sample(range(cfg.days), k=n_v_days))

        day = cfg.start_date
        for day_index in range(cfg.days):
            is_v = day_index in v_days
            values = daily_profile(rng, intervals, uom)

            # A fabricated MDM load time a day or two after the reading.
            update_dt = datetime(day.year, day.month, day.day) + timedelta(
                days=rng.randint(1, 2),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
                seconds=rng.randint(0, 59),
            )

            # 300 record
            write(
                [
                    "300",
                    day.strftime("%Y%m%d"),
                    format_values(values),
                    "V" if is_v else "A",
                    "",  # reason code (300 level is always blank here)
                    "",  # reason description
                    update_dt.strftime("%Y%m%d%H%M%S"),
                    "",  # MSATS load datetime (blank in the reference file)
                ]
            )
            counts["300"] += 1

            if is_v:
                for start, end, quality, reason in make_400_segments(
                    rng, intervals, cfg.segments_per_v_day
                ):
                    # 400 record
                    write(["400", str(start), str(end), quality, reason, ""])
                    counts["400"] += 1

            day += delta_day

    write(["900"])

    counts["readings"] = counts["300"] * intervals
    return counts, bytes_written


def parse_args(argv: list[str] | None = None) -> Config:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=Config.seed, help="RNG seed")
    p.add_argument("--days", type=int, default=Config.days, help="days per channel")
    p.add_argument(
        "--channels", type=int, default=Config.n_channels, help="number of channels"
    )
    p.add_argument(
        "--interval", type=int, default=Config.interval, help="interval minutes"
    )
    p.add_argument(
        "--start",
        default=Config.start_date.isoformat(),
        help="first reading date (YYYY-MM-DD)",
    )
    p.add_argument("--nmi", default=Config.nmi, help="NMI")
    args = p.parse_args(argv)
    return Config(
        seed=args.seed,
        days=args.days,
        n_channels=args.channels,
        interval=args.interval,
        start_date=date.fromisoformat(args.start),
        nmi=args.nmi,
    )


def main(argv: list[str] | None = None) -> None:
    import os
    import sys

    cfg = parse_args(argv)
    counts, bytes_written = generate(cfg, sys.stdout.buffer)
    size_mb = bytes_written / 1e6
    print(f"Wrote ({size_mb:.1f} MB)", file=sys.stderr)
    print(
        f"  200 blocks: {counts['200']}  "
        f"300 rows: {counts['300']}  "
        f"400 rows: {counts['400']}  "
        f"readings: {counts['readings']}",
        file=sys.stderr
    )


if __name__ == "__main__":
    main()
