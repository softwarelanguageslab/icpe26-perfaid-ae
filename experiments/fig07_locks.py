#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Figure 7 Experiment: Lock throughput across KyotoCabinet, LevelDB, RocksDB.

Paper reference:
    Section 4.1 (Studying Locking Impact with perfaid), Figure 7.

What this script does:
    Runs a comprehensive lock sweep across three key-value store benchmarks
    (KyotoCabinet, LevelDB, RocksDB) with two workloads each for LevelDB and
    RocksDB (readrandom, seekrandom), producing a 5-panel figure.

    Eight lock implementations are compared: CAS, TTAS, Ticket, MCS, Hemlock,
    CNA, HMCS, and the default glibc pthread_mutex baseline. Thread counts
    sweep from 1 to 96 (filtered to available CPUs). Each configuration is
    repeated 3 times for 10 seconds.

    The Tilt shared library is built automatically and injected via LD_PRELOAD.

Hardware used in the paper:
    Platform B - NUMA server (2x Kunpeng 920-4826, 96 cores across 4 NUMA
    nodes, 539 GiB RAM, Ubuntu 20.04.6 LTS, kernel 5.4.0-200-generic, aarch64).

    On machines with fewer cores, thread counts are automatically filtered.
    Qualitative trends (e.g., NUMA-aware locks outperforming flat locks at
    high thread counts) may differ on non-NUMA or small-core-count machines.

Expected execution time:
    ~96 minutes on the paper's 96-core server (with duration=5, nb_runs=2).
    Measured: real 95m39s. Scales with core count and number of locks.

Prerequisites:
    - System packages: build-essential, cmake, libsnappy-dev, libgflags-dev,
      liblz4-dev, libzstd-dev, zlib1g-dev (for RocksDB)
    - Python environment set up (see README)

How to run:
    cd experiments/
    python fig07_locks.py

Output:
    - CSV results per panel and line-plots (PNG/PDF) in ~/.benchkit/results/
    - One line plot per panel: throughput vs. threads, one line per lock
"""

from benchkit import CampaignCartesianProduct
from benchkit.benches.kyotocabinet import KyotoCabinetBench
from benchkit.benches.leveldb import LevelDBBench
from benchkit.benches.rocksdb import RocksDBBench
from benchkit.campaign import CampaignSuite

from lib import LOCKS, PRETTY_LOCKS, Panel, get_platform, get_tilt_lib

# Experiment configuration (values used for plot generation in submission)
THREADS = [1, 2, 4, 8, 16, 24, 32, 64, 72, 80, 88, 96]
# NB_RUNS = 3
# DURATION_S = 10

# Parameters reduced for practical concerns:
NB_RUNS = 2
DURATION_S = 5


def main() -> None:
    platform = get_platform()
    tiltlib = get_tilt_lib(platform=platform)

    # Filter thread counts to available CPUs
    max_cpus = platform.nb_cpus()
    threads = [t for t in THREADS if t <= max_cpus]

    # Define the panels (one per benchmark/workload)
    panels = [
        Panel(
            name="kyotocabinet",
            campaign_name="fig07_kyotocabinet",
            bench=KyotoCabinetBench(),
            parameter_space={
                "nb_threads": threads,
                "lock": LOCKS,
            },
        ),
        Panel(
            name="leveldb/readrandom",
            campaign_name="fig07_leveldb_readrandom",
            bench=LevelDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["readrandom"],
                "lock": LOCKS,
            },
        ),
        Panel(
            name="leveldb/seekrandom",
            campaign_name="fig07_leveldb_seekrandom",
            bench=LevelDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["seekrandom"],
                "lock": LOCKS,
            },
        ),
        Panel(
            name="rocksdb/readrandom",
            campaign_name="fig07_rocksdb_readrandom",
            bench=RocksDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["readrandom"],
                "lock": LOCKS,
            },
        ),
        Panel(
            name="rocksdb/seekrandom",
            campaign_name="fig07_rocksdb_seekrandom",
            bench=RocksDBBench(),
            parameter_space={
                "nb_threads": threads,
                "bench_name": ["seekrandom"],
                "lock": LOCKS,
            },
        ),
    ]

    # Create campaigns for each panel
    campaigns = [
        CampaignCartesianProduct(
            name=p.campaign_name,
            benchmark=p.bench,
            shared_libs=[tiltlib],
            variables=p.parameter_space,
            pretty={"lock": PRETTY_LOCKS},
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
            hue="lock",
            title=f"Lock throughput - {panel.name}",
        )

    print("\nResults saved to: ~/.benchkit/results/")


if __name__ == "__main__":
    main()
