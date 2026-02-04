# ssp_bridge/plugins/ams2/plugin.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.plugins.ams2.receiver import LatestUDPReceiver
from ssp_bridge.core.capabilities import CAPABILITIES_AMS2


def _clamp_pct(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 100.0:
        return 100.0
    return x


class AMS2Plugin(TelemetryPlugin):
    id = "ams2"
    name = "Automobilista 2 (UDP/SMS)"

    def __init__(self, udp_port: int = 5606) -> None:
        self._udp_port = int(udp_port)
        self._receiver: Optional[LatestUDPReceiver] = None

    def open(self) -> None:
        # abre receiver UDP
        self._receiver = LatestUDPReceiver(host="0.0.0.0", port=self._udp_port)
        self._receiver.start()

        # IMPORTANTE:
        # Só consideramos "aberto" se chegar pelo menos 1 pacote.
        # Isso faz o --game auto funcionar e o --wait funcionar bem.
        deadline = time.time() + 0.6  # ~600ms
        while time.time() < deadline:
            if self._receiver.get_latest() is not None:
                return
            time.sleep(0.02)

        # Não chegou nada: fecha e sinaliza "simulador não disponível ainda"
        self.close()
        raise RuntimeError(
            f"AMS2 UDP not detected yet (no packets on port {self._udp_port}). "
            f"Enable UDP telemetry in AMS2 and match the port."
        )

    def read_frame(self) -> Optional[Dict[str, Any]]:
        if self._receiver is None:
            raise RuntimeError("AMS2Plugin is not opened. Call open() first.")

        tel = self._receiver.get_latest()
        if tel is None:
            return None

        speed_kmh = abs(tel.speed_ms) * 3.6

        return {
            "v": "0.2",
            "ts": tel.ts,
            "source": "ams2",
            "signals": {
                "engine.rpm": int(tel.rpm),
                "vehicle.speed_kmh": float(speed_kmh),
                "drivetrain.gear": int(tel.gear),
                "controls.throttle_pct": _clamp_pct(float(tel.throttle_pct)),
                "controls.brake_pct": _clamp_pct(float(tel.brake_pct)),
            },
        }

    def capabilities(self) -> Dict[str, Any]:
        return CAPABILITIES_AMS2

    def close(self) -> None:
        if self._receiver is not None:
            self._receiver.stop()
            self._receiver = None
