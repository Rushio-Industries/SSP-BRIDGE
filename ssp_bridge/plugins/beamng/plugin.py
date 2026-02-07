from __future__ import annotations

import time

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.core.capabilities import CAPABILITIES_AC  # reuse base set shape
from ssp_bridge.core.proc import ProcessWatch

from .receiver import LatestOutGaugeReceiver


class BeamNGPlugin(TelemetryPlugin):
    """BeamNG.drive telemetry plugin (official OutGauge UDP).

    IMPORTANT:
    BeamNG OutGauge does not expose a stable vehicle model id.
    To make derived signals (engine.rpm_max / engine.rpm_pct) reset on vehicle swaps,
    we generate a bridge-side vehicle.car_id based on an "idle boundary" heuristic.
    """

    id = "beamng"
    name = "BeamNG.drive"

    def __init__(self) -> None:
        # BeamNG executable is commonly BeamNG.drive.x64.exe on Windows
        self._proc = ProcessWatch(
            "BeamNG.drive.x64.exe",
            cache_ttl=0.75,
            miss_threshold=3,
        )

        # OutGauge receiver (BeamNG configurable; we listen on port 4444 by default)
        self._rx = LatestOutGaugeReceiver(host="0.0.0.0", port=4444)

        # If we don't receive packets for a bit, treat telemetry as stale.
        self._stale_after_s = 0.6

        # Bridge-generated "car identity" (epoch).
        # This changes when we detect a vehicle swap, so rpm_max resets correctly.
        self._car_epoch = 0
        self._idle_since: float | None = None
        self._swap_idle_s = 1.2  # seconds of "idle/off" before we consider it a new car
        self._had_activity = False  # prevents bumping epoch at startup/menu idling

    def open(self) -> None:
        """Start UDP receiver and reset runtime state."""
        self._proc.reset()
        self._rx.start()

        # Reset identity state on open (fresh session)
        self._car_epoch = 0
        self._idle_since = None
        self._had_activity = False

    def _has_live_telemetry(self, tel) -> bool:
        """Conservative filter to avoid false positives (menu/idle packets)."""
        if int(tel.rpm) > 0:
            return True
        if abs(float(tel.speed_ms)) > 0.05:
            return True
        if float(tel.throttle_pct) > 0.5:
            return True
        if float(tel.brake_pct) > 0.5:
            return True
        return False

    def _maybe_bump_car_epoch(self, tel) -> None:
        """Detect vehicle swap and bump bridge car epoch.

        Heuristic:
        During a vehicle change, we often see a short phase where:
          - rpm ~ 0
          - speed ~ 0
          - pedals ~ 0
        If that lasts for `_swap_idle_s`, we bump the epoch ONCE.
        """
        rpm = int(tel.rpm)
        speed_ms = float(tel.speed_ms)
        throttle = float(tel.throttle_pct)
        brake = float(tel.brake_pct)

        # Consider this "idle/off"
        is_idle = (
            rpm < 150 and
            abs(speed_ms) < 0.2 and
            throttle < 1.0 and
            brake < 1.0
        )

        now = time.time()

        # Track if we ever had real activity (prevents bumping during initial idle)
        if not self._had_activity and self._has_live_telemetry(tel):
            self._had_activity = True

        if not self._had_activity:
            # Still in startup/menu idle; do not bump epoch.
            self._idle_since = None
            return

        if is_idle:
            if self._idle_since is None:
                self._idle_since = now
            elif (now - self._idle_since) >= self._swap_idle_s:
                # Vehicle boundary detected -> bump epoch once, then wait for activity.
                self._car_epoch += 1
                self._idle_since = None
        else:
            # Back to active telemetry -> clear idle timer
            self._idle_since = None

    def read_frame(self):
        """Return SSP frame dict, or None if no fresh telemetry yet."""
        if not self._proc.running():
            raise RuntimeError("BeamNG process closed")

        tel = self._rx.get_latest()
        if tel is None:
            return None

        # Staleness guard: prevents repeating an old packet forever
        now = time.time()
        if (now - float(tel.ts)) > self._stale_after_s:
            return None

        # Bump bridge car identity when a vehicle swap is detected
        self._maybe_bump_car_epoch(tel)

        # If you want BeamNG to activate only when useful data exists, keep this:
        if not self._has_live_telemetry(tel):
            return None

        # Map to SSP core signals (v0.2)
        speed_kmh = float(tel.speed_ms) * 3.6
        if speed_kmh < 0.0:
            speed_kmh = 0.0

        throttle = float(tel.throttle_pct)
        if throttle < 0.0:
            throttle = 0.0
        elif throttle > 100.0:
            throttle = 100.0

        brake = float(tel.brake_pct)
        if brake < 0.0:
            brake = 0.0
        elif brake > 100.0:
            brake = 100.0

        signals = {
            "engine.rpm": int(tel.rpm),
            "vehicle.speed_kmh": speed_kmh,
            "drivetrain.gear": int(tel.gear),
            "controls.throttle_pct": throttle,
            "controls.brake_pct": brake,

            # Bridge-generated vehicle id:
            # This changes when we detect a car swap, so derived rpm_max resets correctly.
            "vehicle.car_id": f"beamng:{self._car_epoch}",
        }

        return {
            "v": "0.2",
            "ts": float(tel.ts),
            "source": self.id,
            "signals": signals,
        }

    def capabilities(self):
        """Capabilities map for clients (signals MAY appear in frames)."""
        caps = dict(CAPABILITIES_AC)  # copy shape
        caps["plugin"] = self.id
        caps["schema"] = "ssp/0.2"
        return caps

    def close(self) -> None:
        """Stop UDP receiver."""
        try:
            self._rx.stop()
        except Exception:
            pass
