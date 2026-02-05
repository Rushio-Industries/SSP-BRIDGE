from __future__ import annotations

from typing import Any, Dict, Optional

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.core.capabilities import CAPABILITIES_AC
from .shared_memory import ACSharedMemory


class ACPlugin(TelemetryPlugin):
    """Assetto Corsa telemetry plugin (Windows shared memory)."""

    id = "ac"
    name = "Assetto Corsa"

    def __init__(self) -> None:
        self._sm: Optional[ACSharedMemory] = None

    def open(self) -> None:
        self._sm = ACSharedMemory()
        self._sm.open()

    def read_frame(self) -> Dict[str, Any] | None:
        if self._sm is None:
            raise RuntimeError("ACPlugin is not opened. Call open() first.")
        return self._sm.read()

    def capabilities(self) -> Dict[str, Any]:
        return CAPABILITIES_AC

    def close(self) -> None:
        if self._sm is not None:
            self._sm.close()
            self._sm = None
