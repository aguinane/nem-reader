"""
Benchmarks for parsing.

These run with pytest, but must be run explicitly:

    uv run pytest --no-cov --benchmark-only

To save a run and compare against it later (e.g. after changing code):

    uv run pytest --no-cov --benchmark-only --benchmark-save=my_base
    ls .benchmarks/[platform] # note 0001_my_base.json
    # ... make the change ...
    uv run pytest --no-cov --benchmark-only --benchmark-save=change1 --benchmark-compare=0001

"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from nemreader import NEMFile


@pytest.mark.benchmark(group="nem_data")
def test_nem_data(benchmark: BenchmarkFixture, nem12_file: Path):
    nem_data = benchmark(lambda: NEMFile(nem12_file).nem_data())
    readings = sum(
        len(reads)
        for channels in nem_data.readings.values()
        for reads in channels.values()
    )
    assert readings > 0

@pytest.mark.benchmark(group="get_data_frame_long")
def test_get_data_frame_long(benchmark: BenchmarkFixture, nem12_file: Path):
    df = benchmark(lambda: NEMFile(nem12_file).get_data_frame_long())
    assert df is not None
