#!/usr/bin/env python3
# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
HMCS (Hierarchical MCS) lock generation.

Paper reference:
    Section 4.1 - HMCS is one of the NUMA-aware hierarchical locks evaluated
    in the lock study (Figures 7, 14). See Chabbi et al., PPoPP '15.

This module generates a platform-specific HMCS lock header file from the
``template_hmcs.h`` template. The HMCS lock extends the MCS lock with a
multi-level hierarchy that matches the machine's physical topology (cores,
caches, NUMA nodes, packages), reducing coherence traffic by keeping lock
hand-offs local whenever possible.

The generation process:
1. Accepts a nomenclature string (e.g., "cache-numa-system") describing the
   hierarchy levels and their sizes on the target platform.
2. Computes ``#define`` directives for level sizes, thresholds, and the total
   number of lock nodes.
3. Fills in the ``template_hmcs.h`` template and writes the result to
   ``generatedlocks/include/``.

The resulting header is compiled by the CMakeLists.txt in ``generatedlocks/``
and also ``#include``-d by the CNA lock (``locks/include/numa_cnalock.h``)
for NUMA-node identification.

Key function:
    generate_hmcs_lock()    Generate the HMCS header for a given platform topology.
"""

from pathlib import Path
from string import Template
from typing import Tuple

from .tiltgen import generate_tilt_file

Lock = str


def get_hierarchy_defines(
    total_nb_cpus: int,
    full_nomenc_size: Tuple[Tuple[str, int], ...],
    define_prefix: str,
) -> str:
    """
    Generates hierarchy defines for the given nomenclatures and sizes.

    Args:
        nomenclatures (Tuple[str, ...]): The levels of the hierarchy (e.g., core, cache).
        sizes (Tuple[int, ...]): The sizes for each level.
        define_prefix (str): Prefix for the generated defines.

    Returns:
        str: Generated hierarchy defines as a string.
    """
    full_nomenc_size = [("cpu", total_nb_cpus)] + list(full_nomenc_size)
    nom_sizes = full_nomenc_size[:-1][::-1]  # Remove system level, reverse order
    defines = [f"#define {define_prefix}NB_{name.upper()}S {value}" for name, value in nom_sizes]
    result = "\n".join(defines)
    return result


def get_h_thresholds_defines(h_thresholds: Tuple[int, ...]) -> str:
    """
    Generates H-threshold defines for the given thresholds.

    Args:
        h_thresholds (Tuple[int, ...]): Threshold values for each level.

    Returns:
        str: Generated threshold defines as a string.
    """
    defines = [f"#define H{i} {v}" for i, v in enumerate(h_thresholds, start=1)]
    result = "\n".join(defines)
    return result


def generate_hmcs_lock(
    vsync_dir: Path,
    hmcs_spec: str,
    target_directory: Path,
    nomenclature: str,
    sizes: Tuple[int, ...],
    h_thresholds: Tuple[int, ...],
    total_nb_cpus: int,
    total_nb_cores: int,
    full_nomenc_size: Tuple[Tuple[str, int], ...],
) -> Lock:
    """
    Generates the HMCS lock configuration file.

    Args:
        hmcs_spec (str): Specification name for the HMCS lock.
        target_directory (Path): Directory to save the generated file.
        nomenclature (str): Hyphen-separated hierarchy levels.
        sizes (Tuple[int, ...]): Sizes for each hierarchy level.
        h_thresholds (Tuple[int, ...]): Threshold values for each level.
        total_nb_cpus (int): Total number of CPUs in the system.

    Returns:
        Lock: The specification name of the generated HMCS lock.
    """
    template_hmcs_file = Path(__file__).parent / "template_hmcs.h"

    nomenclatures = tuple(nomenclature.split("-"))
    nb_levels = len(nomenclatures)

    hierarchy_defines = get_hierarchy_defines(
        total_nb_cpus=total_nb_cpus,
        full_nomenc_size=full_nomenc_size,
        define_prefix="HMCS_",
    )
    h_thresholds_defines = get_h_thresholds_defines(h_thresholds=h_thresholds)

    level_sizes = "\n".join(
        f"#define LEVEL_{level_nb} {level_size}  /* {level_name} level */"
        for level_nb, level_name, level_size in zip(
            range(1, nb_levels + 1), nomenclatures[::-1], sizes[::-1]
        )
    )

    nb_cpus = total_nb_cpus
    leaf_level = nomenclatures[0]
    leaf_size = sizes[0]
    nb_cpus_per_node = nb_cpus // leaf_size
    cpus_per_leaf_node = (
        f"{nb_cpus_per_node}  "
        f"/* cpus per {leaf_level} "
        f"= nb_cpus / nb_{leaf_level}s "
        f"= {nb_cpus} / {leaf_size} "
        f"= {nb_cpus_per_node} */"
    )

    thresholds_values = ["1"] + [f"H{i}" for i in range(1, nb_levels)]
    thresholds = "\n".join(
        f"#define LEVEL_{i}_THRESHOLD {v}" for i, v in enumerate(thresholds_values, start=1)
    )

    num_locks_sep = " + \\\n"
    indent = "    "
    num_locks = (
        num_locks_sep.join(
            f"{indent}(" + " * ".join(f"LEVEL_{l2}" for l2 in range(1, l1 + 1)) + ")"
            for l1 in range(nb_levels, 0, -1)
        )
        + " \\"
    )

    level_spec = "\n".join(
        f"{indent}{{LEVEL_{i}, LEVEL_{i}_THRESHOLD}}, \\" for i in range(1, nb_levels + 1)
    )

    spinlock_dir = vsync_dir / "include" / "vsync" / "spinlock"
    hmcs_filecontent = (
        Template(template_hmcs_file.read_text())
        .substitute(
            hierarchy_defines=hierarchy_defines,
            h_thresholds_defines=h_thresholds_defines,
            nb_levels=nb_levels,
            level_sizes=level_sizes,
            cpus_per_leaf_node=cpus_per_leaf_node,
            thresholds=thresholds,
            num_locks=num_locks,
            level_spec=level_spec,
            SPINLOCK_INCLUDE_PATH=f"{spinlock_dir}",
            LOCK="hmcslock",
            total_nb_cores=total_nb_cores,
        )
        .strip()
    )

    hmcs_pathname = target_directory / f"{hmcs_spec}.h"

    target_directory.mkdir(parents=True, exist_ok=True)
    hmcs_pathname.write_text(hmcs_filecontent + "\n")

    return hmcs_spec


def main():
    lock_name = "numa_hmcslock"

    repo_dir = Path(__file__).parent.parent.parent.parent.resolve()
    vsync_dir = (repo_dir / "deps/libvsync").resolve()
    hmcs_gen_dir = (repo_dir / "generatedlocks/include").resolve()
    output_dir = (repo_dir / "generatedlocks/src").resolve()

    generate_hmcs_lock(
        vsync_dir=vsync_dir,
        hmcs_spec="hmcs-mcs-mcs-mcs-skp-mcs",
        target_directory=hmcs_gen_dir,
        nomenclature="core-cache-numa-system",
        sizes=(64, 32, 4, 1),
        h_thresholds=(128, 128, 128),
        total_nb_cpus=128,
        total_nb_cores=64,
        full_nomenc_size=(
            ("core", 64),
            ("cache", 32),
            ("numa", 4),
            ("package", 2),
            ("system", 1),
        ),
    )

    Path(hmcs_gen_dir / "hmcs-mcs-mcs-mcs-skp-mcs.h").rename(hmcs_gen_dir / "numa_hmcslock.h")

    try:
        generate_tilt_file(
            lock_name=lock_name,
            lock_header_dir=hmcs_gen_dir,
            output_dir=output_dir,
            include_path="vsync/spinlock",
        )
    except Exception as e:
        print(f"Failed to generate tilt file for {lock_name}: {e}")


if __name__ == "__main__":
    main()
