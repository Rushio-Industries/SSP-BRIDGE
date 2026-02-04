from __future__ import annotations

import time

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.core.capabilities import CAPABILITIES_ACC
from ssp_bridge.core.proc import ProcessWatch
from .shared_memory import ACCSharedMemory


class ACCPlugin(TelemetryPlugin):
    """Assetto Corsa Competizione telemetry plugin (Windows shared memory)."""

    id = "acc"
    name = "Assetto Corsa Competizione"

    def __init__(self) -> None:
        self._sm: ACCSharedMemory | None = None

        # Process-aware health check (cached). Using tasklist per frame is too expensive.
        self._proc = ProcessWatch(
            "AC2-Win64-Shipping.exe",
            cache_ttl=0.75,
            miss_threshold=3,
        )

        self._opened_at = 0.0

    def open(self) -> None:
        """Open shared memory mapping and reset runtime state."""
        self._sm = ACCSharedMemory()
        self._sm.open()

        # Reset ProcessWatch internal cache so it re-checks cleanly.
        # (Keeps behavior stable when switching sims in auto mode.)
        self._proc._misses = 0
        self._proc._cached_running = True
        self._proc._last_check_ts = 0.0

        self._opened_at = time.time()

    def read_frame(self):
        """
        Read the latest ACC telemetry snapshot.

        Runtime rules:
        - If the ACC process is not running, raise to trigger 'lost' and auto-detect recovery.
        - If no valid telemetry is available yet, return None (do not spam duplicates).
        - Do NOT use packetId as a liveness signal: ACC can legitimately keep packetId stable
          during loading, pause, menus, and some transitions.
        """
        if not self._proc.running():
            raise RuntimeError("ACC process closed")

        if self._sm is None:
            raise RuntimeError("ACCPlugin is not opened. Call open() first.")

        data = self._sm.read()
        if not data:
            return None

        return data

    def capabilities(self):
        """Return SSP capabilities for ACC."""
        return CAPABILITIES_ACC

    def close(self) -> None:
        """Close shared memory mapping."""
        if self._sm:
            self._sm.close()
            self._sm = None
