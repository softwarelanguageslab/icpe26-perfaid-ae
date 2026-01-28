#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Figure 15 Experiment: perfaid framework overhead measurement.

Paper reference:
    Section 5 (Overhead of perfaid), Figure 15.

What this script does:
    Measures perfaid's overhead by running LevelDB readrandom on both the
    native host and inside a Docker container, then comparing throughput
    with equivalent hand-written shell scripts (shell_host.sh, shell_docker.sh).

    The script:
    1. Builds a Docker image (perfaid_overhead) using pythainer
    2. Runs a benchkit campaign on the host (fig15_leveldb_host)
    3. Runs a benchkit campaign inside Docker (fig15_leveldb_docker)
    4. Generates a strip plot comparing host vs. Docker throughput

    After this script completes, run shell_host.sh and shell_docker.sh to
    produce the shell baseline data, then run plot_overhead.py to generate
    the final 3-panel comparison figure (Figure 15 in the paper).

    The paper shows that perfaid introduces no measurable overhead (<2.2%)
    compared to equivalent hand-written shell scripts.

Hardware used in the paper:
    Intel Core i7-13800H laptop, Ubuntu 22.04.5, Linux 6.8.0.
    Works on any Linux machine with Docker installed.

Expected execution time:
    ~15-20 minutes total:
      - Docker image build: ~2 minutes (first time only)
      - benchkit host campaign: ~5 minutes (3 threads x 10 runs x 10 s)
      - benchkit Docker campaign: ~5 minutes (same)

Prerequisites:
    - System packages: build-essential, cmake, libsnappy-dev
    - Docker installed and current user in docker group
    - Python environment set up (see README)

How to run (full Figure 15 reproduction):
    cd experiments/fig15_overhead/

    # Step 1: Run benchkit campaigns (host + Docker)
    python fig15_leveldb_overhead.py

    # Step 2: Run shell baselines
    ./shell_host.sh
    ./shell_docker.sh

    # Step 3: Generate the final comparison plot
    python plot_overhead.py

Output:
    - Campaign CSVs in ~/.benchkit/results/
    - Shell results in ~/.benchkit/results/fig15_shell_{host,docker}/
    - Final figure: ~/.benchkit/results/fig15_overhead.{pdf,png}
"""

from pathlib import Path

from benchkit import CampaignCartesianProduct
from benchkit.benches.leveldb import LevelDBBench
from benchkit.campaign import CampaignSuite
from benchkit.communication.docker import DockerCommLayer
from benchkit.platforms import Platform
from benchkit.utils.dir import benchkit_home_dir, gitmainrootdir
from pythainer.examples.builders import get_user_builder
from pythainer.runners import ConcreteDockerRunner

from lib import get_platform

# Note: Run this script before shell_host.sh/shell_docker.sh, as it builds the
# Docker image and clones the LevelDB repository that the shell scripts reuse.
# See the README for pythainer documentation.


# Experiment configuration
NB_RUNS = 10
DURATION_S = 10
THREADS = [2, 4, 8]


def _get_os_version() -> str:
    """Get the current OS version for Docker base image."""
    osinfo = {}
    with open("/etc/os-release") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                osinfo[k] = v.strip('"')
    return f"{osinfo['ID']}:{osinfo['VERSION_ID']}"


def _get_docker_platform() -> Platform:
    """Create a Docker platform for container experiments."""
    image_name = "perfaid_overhead"
    work_dir = "/home/user/workspace"
    docker_path = Path(work_dir)
    repo_dir = gitmainrootdir().resolve()

    # Build Docker image
    builder = get_user_builder(
        image_name=image_name,
        base_ubuntu_image=_get_os_version(),
    )
    builder.root()
    builder.add_packages(packages=["libsnappy-dev"])
    builder.user()
    builder.workdir(path=work_dir)
    builder.build()

    # Configure volume mounts
    host_benchkit_dir = benchkit_home_dir().expanduser() / "docker"
    dock_benchkit_dir = benchkit_home_dir().expanduser()
    host_benchkit_dir.mkdir(parents=True, exist_ok=True)

    runner = ConcreteDockerRunner(
        image=image_name,
        name="container",
        volumes={
            f"{repo_dir}": f"{docker_path}",
            f"{host_benchkit_dir}": f"{dock_benchkit_dir}",
        },
    )

    comm = DockerCommLayer(docker_runner=runner)
    platform = Platform(comm_layer=comm)
    return platform


def _get_campaign(
    name: str,
    run_type: str,
    platform: Platform,
):
    """Create a LevelDB campaign for the given platform."""
    return CampaignCartesianProduct(
        name=name,
        benchmark=LevelDBBench(),
        nb_runs=NB_RUNS,
        variables={
            "bench_name": ["readrandom"],
            "nb_threads": THREADS,
        },
        constants={
            "run_type": run_type,
        },
        duration_s=DURATION_S,
        platform=platform,
    )


def main() -> None:
    host_platform = get_platform()
    docker_platform = _get_docker_platform()

    suite = CampaignSuite(
        campaigns=[
            _get_campaign(
                name="fig15_leveldb_docker",
                run_type="benchkit_docker",
                platform=docker_platform,
            ),
            _get_campaign(
                name="fig15_leveldb_host",
                run_type="benchkit_host",
                platform=host_platform,
            ),
        ]
    )

    suite.print_durations()
    suite.run_suite()

    suite.generate_graph(
        plot_name="stripplot",
        x="nb_threads",
        y="throughput",
        hue="run_type",
        title="benchkit throughput comparison between Docker container and host",
    )

    print("\nResults saved to: ~/.benchkit/results/")
    print("\nTo compare with shell scripts, run:")
    print("  ./shell_host.sh")
    print("  ./shell_docker.sh")


if __name__ == "__main__":
    main()
