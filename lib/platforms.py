# Copyright (C) 2024 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Platform detection and configuration.

This module provides platform detection that recognizes known server
configurations used in the paper and falls back to auto-detection for
unknown machines.

Known platforms:
    "algol"     Taishan 200, 2x Kunpeng 920-4826 (96 cores, 4 NUMA nodes,
                aarch64). This is Platform B in the paper (Section 4).

For any other hostname, ``get_current_platform()`` from benchkit is used,
which auto-detects the CPU topology (core count, NUMA layout, cache
structure) from the local machine. This allows all scripts to run on
arbitrary hardware without manual configuration.
"""

from benchkit.communication import LocalCommLayer
from benchkit.platforms import Platform, get_current_platform
from benchkit.platforms.servers import Taishan200Kunpeng9204826x2
from benchkit.utils.misc import hostname

# Known platform configurations (hostname -> Platform class)
_KNOWN_PLATFORMS = {
    "algol": Taishan200Kunpeng9204826x2,
}


def get_platform() -> Platform:
    """
    Get the platform for the current machine.

    Returns a specialized Platform instance for known machines (e.g., NUMA servers),
    or auto-detects the platform for unknown machines.

    Returns:
        Platform instance configured for the current machine.
    """
    host = hostname()

    if host in _KNOWN_PLATFORMS:
        comm_layer = LocalCommLayer()
        platform = _KNOWN_PLATFORMS[host](comm_layer=comm_layer)
        return platform

    return get_current_platform()
