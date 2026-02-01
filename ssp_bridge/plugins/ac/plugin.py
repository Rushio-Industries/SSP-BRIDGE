from __future__ import annotations

from typing import Any, Dict

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.plugins.ac.shared_memory import ACPhysicsView
from ssp_bridge.core.frame import to_ssp_frame_ac
from ssp_bridge.core.capabilities import CAPABILITIES_AC_V01


class ACPlugin(TelemetryPlugin):
    id = "ac"
    name = "Assetto Corsa"

    def __init__(self) -> None:
        self._phys: ACPhysicsView | None = None

    def open(self) -> None:
        self._phys = ACPhysicsView()

    def read_frame(self) -> Dict[str, Any]:
        if self._phys is None:
            raise RuntimeError("ACPlugin is not opened. Call open() first.")
        return to_ssp_frame_ac(self._phys.data)

    def capabilities(self) -> Dict[str, Any]:
        return CAPABILITIES_AC_V01

    def close(self) -> None:
        if self._phys is not None:
            self._phys.close()
            self._phys = None
