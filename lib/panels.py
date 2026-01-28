# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Panel dataclass for organizing multi-panel experiment figures.

Paper reference:
    Used by Figures 7 and 10, which each produce 5-panel comparison plots
    across KyotoCabinet, LevelDB/readrandom, LevelDB/seekrandom,
    RocksDB/readrandom, and RocksDB/seekrandom.

A Panel groups together a benchmark instance, its parameter space, and
display metadata (panel title, campaign output name). The experiment scripts
(fig07_locks.py, fig10_schedulers.py) create a list of Panel objects and
iterate over them to build one CampaignCartesianProduct per panel, all
coordinated by a CampaignSuite.
"""

from dataclasses import dataclass
from typing import Any, Iterable

from benchkit.core.benchmark import Benchmark


@dataclass(frozen=True)
class Panel:
    """
    A single panel in a multi-panel experiment figure.

    Attributes:
        name: Human-readable name for the panel (e.g., "leveldb/readrandom").
        campaign_name: Name used for benchkit output directories and CSV files.
        bench: The benchkit Benchmark instance to run.
        parameter_space: Dictionary mapping variable names to their values.
    """

    name: str
    campaign_name: str
    bench: Benchmark
    parameter_space: dict[str, Iterable[Any]]
