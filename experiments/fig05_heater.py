#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Figure 5 Experiment (right panel): Sequential heater per-CPU characterization.

Paper reference:
    Section 3.2 (Sequential CPU-ID Characterization), Figure 5 (right).

What this script does:
    Runs the sequential heater benchmark pinned to each logical CPU in turn,
    producing a bar chart of per-core throughput. On hybrid-core processors,
    this reveals two distinct plateaus corresponding to P-cores and E-cores.
    The resulting core-to-speed mapping is used to configure P_CORES / E_CORES
    for the placement experiments (fig05_placement_spec.py, fig05_placement_leveldb.py).

Hardware used in the paper:
    Platform A - hybrid-core laptop (AMD Ryzen AI 9 HX 370, 24 cores).
    Works on any Linux machine; homogeneous machines show a flat bar chart.

Expected execution time:
    ~3 minutes on a 24-core machine (24 CPUs x 3 runs x 3 s = 216 s).

Prerequisites:
    - System packages: build-essential, cmake
    - Python environment set up (see README)

How to run:
    cd experiments/
    python fig05_heater.py

Output:
    - CSV results and a bar-plot (PNG/PDF) in ~/.benchkit/results/
    - Bar plot shows per-CPU operations count, revealing P/E core asymmetry
"""

import os

from benchkit.benches.heater.sequential import heater_seq_campaign


def main() -> None:
    # Create a campaign that runs the heater on each CPU
    campaign = heater_seq_campaign(
        name="fig05_heater",
        nb_runs=3,
        duration_s=3,
        cpu=range(0, os.cpu_count()),
    )

    # Execute the campaign
    campaign.run()

    # Generate a bar plot showing per-CPU throughput
    campaign.generate_graph(
        plot_name="barplot",
        x="cpu",
        y="ops",
        title="Sequential heater - per-CPU throughput",
    )


if __name__ == "__main__":
    main()
