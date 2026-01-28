#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Figure 5 Experiment (left panel, open-source alternative): Hybrid-core variability.

Paper reference:
    Section 3.3 (Controlled Placement with taskset), Figure 5 (left).

What this script does:
    Reproduces the placement experiment from Figure 5 (left) using LevelDB as
    an open-source alternative to SPEC CPU 2017 perlbench_r. It runs LevelDB
    readrandom under three CPU placements (No Pinning, P-Cores, E-Cores) with
    100 repetitions each, producing a strip plot that shows throughput variability.

    The paper's Figure 5 (left) uses SPEC CPU 2017 - see fig05_placement_spec.py for that
    version (requires a SPEC license). This script demonstrates the same
    methodology and perfaid features without proprietary dependencies.

Hardware used in the paper:
    Platform A - hybrid-core laptop (AMD Ryzen AI 9 HX 370, 8 P-cores + 16
    E-cores, 24 total, 32 GiB RAM, Manjaro 26.0.1, Linux 6.18+).
    Adjust P_CORES / E_CORES for your hardware. Run examples/fig03_heater.py
    first to identify which cores are P vs. E.

Expected execution time:
    ~5 minutes (3 placements x 100 runs, each run is short: 40 000 iterations).

Prerequisites:
    - System packages: build-essential, cmake, libsnappy-dev
    - Python environment set up (see README)
    - Adjust P_CORES / E_CORES constants below for your CPU

How to run:
    cd experiments/
    python fig05_placement_leveldb.py

Output:
    - CSV results and a strip-plot (PNG/PDF) in ~/.benchkit/results/
    - Strip plot shows throughput by CPU placement condition
"""

from benchkit import CampaignCartesianProduct
from benchkit.benches.leveldb import LevelDBBench
from benchkit.commandwrappers.taskset import TasksetWrap

# CPU configuration for AMD Ryzen AI 9 HX 370
# Adjust these for your specific hybrid-core processor.
# Use fig03_heater.py to identify P-cores (high throughput) vs E-cores (lower throughput).
P_CORES = [0, 1, 2, 3, 12, 13, 14, 15]
E_CORES = [4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 21, 22, 23]


def main() -> None:
    campaign = CampaignCartesianProduct(
        name="fig05_placement_leveldb",
        benchmark=LevelDBBench(),
        variables={
            "bench_name": ["readrandom"],
            "nb_threads": [1],
            "nb_iterations": [40000],
            "cpu_list": {
                "no_pinning": [],  # Let the scheduler decide
                "p_cores": P_CORES,  # Pin to P-cores only
                "e_cores": E_CORES,  # Pin to E-cores only
            },
        },
        command_wrappers=[TasksetWrap(set_all_cpus=True)],
        nb_runs=100,
        pretty={
            "cpu_list": {
                "__category__": "CPU Placement",
                "no_pinning": "No Pinning",
                "p_cores": "P-Cores",
                "e_cores": "E-Cores",
            },
            "operations/second": "Throughput (ops/s)",
        },
    )

    campaign.run()

    campaign.generate_graph(
        plot_name="stripplot",
        x="CPU Placement",
        y="Throughput (ops/s)",
        hue="CPU Placement",
        title="LevelDB readrandom - throughput variability by placement",
    )


if __name__ == "__main__":
    main()
