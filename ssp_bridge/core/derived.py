# ssp_bridge/core/derived.py
from __future__ import annotations

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class RpmMaxTracker:
    """
    Tracks engine.rpm_max by observing peak RPM.

    New:
    - Resets automatically when vehicle.car_id changes.
    """
    def __init__(self, publish_min_rpm: int = 3000) -> None:
        self.publish_min_rpm = publish_min_rpm
        self.max_rpm: int = 0
        self._car_id: str | None = None

    def reset(self) -> None:
        self.max_rpm = 0

    def update_car(self, car_id: str | None) -> None:
        if car_id is None:
            return

        if self._car_id != car_id:
            self._car_id = car_id
            self.reset()

    def update(self, rpm: int) -> None:
        if rpm > self.max_rpm:
            self.max_rpm = rpm

    def ready(self) -> bool:
        return self.max_rpm >= self.publish_min_rpm


def add_engine_rpm_pct(signals: dict, tracker: RpmMaxTracker) -> None:
    # --- car id handling ---
    car_id = signals.get("vehicle.car_id")
    tracker.update_car(car_id)

    # --- rpm handling ---
    rpm = signals.get("engine.rpm")
    if rpm is None:
        return

    try:
        rpm_i = int(rpm)
    except Exception:
        return

    tracker.update(rpm_i)

    if not tracker.ready():
        return

    rpm_max = tracker.max_rpm
    if rpm_max <= 0:
        return

    rpm_ratio = clamp(float(rpm_i) / float(rpm_max), 0.0, 1.0)

    signals["engine.rpm_max"] = int(rpm_max)
    signals["engine.rpm_pct"] = round(rpm_ratio, 3)
