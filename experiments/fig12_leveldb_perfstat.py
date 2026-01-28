#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Figure 12 Experiment: perf-stat analysis for LevelDB with schedulers.

Paper reference:
    Section 4.3 (Using perf for Profiling and Run-Time Statistics), Figure 12.

What this script does:
    Runs LevelDB readrandom at 24 threads under six scheduling policies while
    collecting hardware performance counters via `perf stat`. The campaign
    produces a 5-panel bar chart: throughput, context-switches, cpu-migrations,
    page-faults, and cache-misses.

    Each policy is run 3 times for 30 seconds, with perf stat collecting
    system-wide events. The PerfStatWrap wrapper and its post-run hook
    handle perf invocation and result parsing automatically.

Hardware used in the paper:
    Platform B - NUMA server (2x Kunpeng 920-4826, 96 cores across 4 NUMA
    nodes, 539 GiB RAM, Ubuntu 20.04.6 LTS, kernel 5.4.0-200-generic, aarch64).

Expected execution time:
    ~10 minutes (6 schedulers x 3 runs x 30 s = 540 s).
    Measured on paper hardware: real 9m58s.

Prerequisites:
    - System packages: build-essential, cmake, libsnappy-dev, linux-tools-*
    - Perf access: sudo sysctl -w kernel.perf_event_paranoid=-1
    - Python environment set up (see README)

How to run:
    cd experiments/
    python fig12_leveldb_perfstat.py

Output:
    - CSV results and bar-plots (PNG/PDF) in ~/.benchkit/results/
    - Five bar plots: throughput + four perf-stat metrics, one bar per scheduler
"""

from benchkit import CampaignCartesianProduct
from benchkit.benches.leveldb import LevelDBBench
from benchkit.commandwrappers.perf import PerfStatWrap, enable_non_sudo_perf

from lib import PRETTY_SCHEDULERS, SCHEDULERS, get_platform, get_scheduler

# Experiment configuration
NB_THREADS = 24
NB_RUNS = 3
DURATION_S = 30


def main() -> None:
    platform = get_platform()

    # Enable perf without sudo (best-effort)
    enable_non_sudo_perf(comm_layer=platform.comm)

    schedkit = get_scheduler(platform=platform)

    # Configure perf stat
    perf_stat = PerfStatWrap(
        events=[
            "context-switches",
            "cpu-migrations",
            "page-faults",
            "cache-misses",
        ],
        use_json=False,
        separator=";",
        aggregate_hybrid=True,
    )

    campaign = CampaignCartesianProduct(
        name="fig12_leveldb_perfstat",
        benchmark=LevelDBBench(),
        variables={
            "nb_threads": [NB_THREADS],
            "bench_name": ["readrandom"],
            "scheduler": SCHEDULERS,
        },
        pretty={"scheduler": PRETTY_SCHEDULERS},
        nb_runs=NB_RUNS,
        duration_s=DURATION_S,
        command_wrappers=[perf_stat],
        pre_run_hooks=[schedkit.start_sched_hook],
        post_run_hooks=[
            schedkit.end_sched_hook,
            perf_stat.post_run_hook_update_results,
        ],
        platform=platform,
    )

    campaign.run()

    # Generate all 5 panels
    metrics = [
        ("throughput", "Throughput"),
        ("perf-stat/context-switches", "Context Switches"),
        ("perf-stat/cpu-migrations", "CPU Migrations"),
        ("perf-stat/page-faults", "Page Faults"),
        ("perf-stat/cache-misses", "Cache Misses"),
    ]

    for metric, title in metrics:
        campaign.generate_graph(
            plot_name="barplot",
            x="scheduler",
            y=metric,
            hue="scheduler",
            title=title,
        )

    print("\nResults saved to: ~/.benchkit/results/")


if __name__ == "__main__":
    main()
