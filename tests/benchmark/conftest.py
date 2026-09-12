from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def nem12_file(tmp_path_factory) -> Path:
    override = os.environ.get("NEM_BENCH_FILE")
    if override:
        return Path(override)

    from generate_big_nem12 import Config, generate

    out = tmp_path_factory.mktemp("nem12") / "bench.csv"
    with open(out, "wb") as fh:
        generate(Config(days=365), fh)
    return Path(out)
