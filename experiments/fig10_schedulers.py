#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Figure 10 Experiment: Scheduler throughput across KyotoCabinet, LevelDB, RocksDB.

Paper reference:
    Section 4.2 (Studying Thread-Placement Impact with perfaid), Figure 10.

What this script does:
    Runs a comprehensive scheduler sweep across three key-value store benchmarks
    (KyotoCabinet, LevelDB, RocksDB) with two workloads each for LevelDB and
    RocksDB (readrandom, seekrandom), producing a 5-panel figure.

    Six scheduling policies are compared: Normal (default Linux), FAR, CLOSE,
    AsymSched, SAM, and SAS. Thread counts sweep from 1 to 96 (filtered to
    available CPUs). Each configuration is repeated 3 times for 10 seconds.

    The schedkit (UserPlace) daemon is managed via pre/post-run hooks.

Hardware used in the paper:
    Platform B - NUMA server (2x Kunpeng 920-4826, 96 cores across 4 NUMA
    nodes, 539 GiB RAM, Ubuntu 20.04.6 LTS, kernel 5.4.0-200-generic, aarch64).

    On non-NUMA machines, the NUMA-aware policies may not show meaningful
    differences compared to the default Linux scheduler.

Expected execution time:
    ~96 minutes on the paper's 96-core server (with duration=5, nb_runs=2).
    Measured: real 95m26s. Scales with core count and number of schedulers.

Prerequisites:
    - System packages: build-essential, cmake, libsnappy-dev, libgflags-dev,
      liblz4-dev, libzstd-dev, zlib1g-dev (for RocksDB)
    - Python environment set up (see README)

How to run:
    cd experiments/
    python fig10_schedulers.py

Output:
    - CSV results per panel and line-plots (PNG/PDF) in ~/.benchkit/results/
    - One line plot per panel: throughput vs. threads, one line per scheduler
"""

from benchkit import CampaignCartesianProduct
from benchkit.benches.kyotocabinet import KyotoCabinetBench
from benchkit.benches.leveldb import LevelDBBench
from benchkit.benches.rocksdb import RocksDBBench
from benchkit.campaign import CampaignSuite

from lib import PRETTY_SCHEDULERS, SCHEDULERS, Panel, get_platform, get_scheduler

# Experiment configuration (values used for plot generation in submission)
THREADS = [1, 2, 4, 8, 16, 24, 32, 64, 72, 80, 88, 96]
# NB_RUNS = 3
# DURATION_S = 10

# Parameters reduced for practical concerns:
NB_RUNS = 2
DURATION_S = 5


def main() -> None:
    platform = get_platform()
    schedkit = get_scheduler(platform=platform)

    # Filter thread counts to available CPUs
    max_cpus = platform.nb_cpus()
    threads = [t for t in THREADS if t <= max_cpus]

    # Define the panels (one per benchmark/workload)
    panels = [
        Panel(
            name="kyotocabinet",
            campaign_name="fig10_kyotocabinet",
            bench=KyotoCabinetBench(),
            parameter_space={
                "nb_threads": threads,
                "scheduler": SCHEDULERS,
            },
        ),
        Panel(
            name="leveldb/readrandom",
            campaign_name="fig10_leveldb_readrandom",
            bench=LevelDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["readrandom"],
                "scheduler": SCHEDULERS,
            },
        ),
        Panel(
            name="leveldb/seekrandom",
            campaign_name="fig10_leveldb_seekrandom",
            bench=LevelDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["seekrandom"],
                "scheduler": SCHEDULERS,
            },
        ),
        Panel(
            name="rocksdb/readrandom",
            campaign_name="fig10_rocksdb_readrandom",
            bench=RocksDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["readrandom"],
                "scheduler": SCHEDULERS,
            },
        ),
        Panel(
            name="rocksdb/seekrandom",
            campaign_name="fig10_rocksdb_seekrandom",
            bench=RocksDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["seekrandom"],
                "scheduler": SCHEDULERS,
            },
        ),
    ]

    # Create campaigns for each panel
    campaigns = [
        CampaignCartesianProduct(
            name=p.campaign_name,
            benchmark=p.bench,
            pre_run_hooks=[schedkit.start_sched_hook],
            post_run_hooks=[schedkit.end_sched_hook],
            variables=p.parameter_space,
            pretty={"scheduler": PRETTY_SCHEDULERS},
            nb_runs=NB_RUNS,
            duration_s=DURATION_S,
            platform=platform,
        )
        for p in panels
    ]

    # Run all campaigns
    suite = CampaignSuite(campaigns=campaigns)
    suite.print_durations()
    suite.run_suite()

    # Generate individual graphs for each panel
    for panel, campaign in zip(panels, campaigns):
        campaign.generate_graph(
            plot_name="lineplot",
            x="nb_threads",
            y="throughput",
            hue="scheduler",
            title=f"Scheduler throughput - {panel.name}",
        )

    print("\nResults saved to: ~/.benchkit/results/")


if __name__ == "__main__":
    main()
