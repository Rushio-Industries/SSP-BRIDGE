from __future__ import annotations

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.core.capabilities import CAPABILITIES_ACC
from .shared_memory import ACCSharedMemory


class ACCPlugin(TelemetryPlugin):
    id = "acc"
    name = "Assetto Corsa Competizione"

    def __init__(self) -> None:
        self._sm: ACCSharedMemory | None = None

    def open(self) -> None:
        self._sm = ACCSharedMemory()
        self._sm.open()

    def read_frame(self):
        if self._sm is None:
            raise RuntimeError("ACCPlugin is not opened. Call open() first.")
        data = self._sm.read()
        if not data:
            return None
        return data

    def capabilities(self):
        # Keep the same format across all plugins.
        return CAPABILITIES_ACC

    def close(self) -> None:
        if self._sm:
            self._sm.close()
            self._sm = None
