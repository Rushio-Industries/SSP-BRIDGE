"""AC telemetry plugin.

Reads Assetto Corsa shared memory and normalizes frames for SSP-BRIDGE outputs."""
from __future__ import annotations

import sys
import subprocess
import time
from typing import Any, Dict, Optional

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.plugins.ac.shared_memory import ACPhysicsView
from ssp_bridge.core.frame import to_ssp_frame_ac
from ssp_bridge.core.capabilities import CAPABILITIES_AC


def _proc_running_windows(image_name: str) -> bool:
    """Check whether a process is running on Windows via tasklist."""
    if sys.platform != "win32":
        return True
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {image_name}", "/FO", "CSV", "/NH"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        out = out.strip().lower()
        return (image_name.lower() in out) and ("no tasks" not in out)
    except Exception:
        return True

# --- Plugin Class ---

class ACPlugin(TelemetryPlugin):
    id = "ac"
    name = "Assetto Corsa"

    def __init__(self) -> None:
        self._phys: ACPhysicsView | None = None
        self._last_pkt: Optional[int] = None
        self._last_pkt_change_ts: float = 0.0

    def open(self) -> None:
        self._phys = ACPhysicsView()
        now = time.time()
        self._last_pkt = None
        self._last_pkt_change_ts = now

    def read_frame(self) -> Optional[Dict[str, Any]]:
        # 1. Check if process is running (Windows only).
        if sys.platform == "win32" and not _proc_running_windows("acs.exe"):
            raise RuntimeError("AC process closed")

        if self._phys is None:
            raise RuntimeError("ACPlugin is not opened. Call open() first.")

        now = time.time()
        phys = self._phys.data

        pkt = int(getattr(phys, "packetId", 0))
        rpm = int(getattr(phys, "rpms", 0))
        speed = float(getattr(phys, "speedKmh", 0.0))
        gas = float(getattr(phys, "gas", 0.0))
        brk = float(getattr(phys, "brake", 0.0))

        # Packet watchdog update.
        if self._last_pkt is None:
            self._last_pkt = pkt
            self._last_pkt_change_ts = now
        elif pkt != self._last_pkt:
            self._last_pkt = pkt
            self._last_pkt_change_ts = now

        # Liveness heuristic: consider AC "alive" if the engine is running, 
        # the car is moving, or there is pedal input.
        alive = (
            (pkt > 0)
            and (
                rpm > 200
                or abs(speed) > 1.0
                or gas > 0.05
                or brk > 0.05
            )
        )

        if not alive:
            # If packetId does not change for >2s while not "alive", 
            # force a close to avoid stale shared-memory data from previous sessions.
            if (now - self._last_pkt_change_ts) > 2.0:
                raise RuntimeError("AC mapping stale (packetId not changing). Reopen needed.")
            return None

        return to_ssp_frame_ac(phys)

    def capabilities(self) -> Dict[str, Any]:
        return CAPABILITIES_AC

    def close(self) -> None:
        if self._phys is not None:
            self._phys.close()
            self._phys = None

        self._last_pkt = None
        self._last_pkt_change_ts = 0.0