# ssp_bridge/core/frame.py
from __future__ import annotations

import math
import time
from typing import Any, Dict, Optional


def _now_ts() -> float:
    """Unix timestamp em segundos (float)."""
    return time.time()


def _clamp_pct(x: float) -> float:
    """Garante 0..100 (ajuda a evitar valores malucos se algo estiver desalinhado)."""
    if x < 0.0:
        return 0.0
    if x > 100.0:
        return 100.0
    return x


def _speed_kmh_from_velocity(phys: Any) -> float:
    """
    Fallback robusto: usa o vetor velocity (m/s) do AC.
    speed = sqrt(vx^2 + vy^2 + vz^2) * 3.6
    """
    vx = float(phys.velocity[0])
    vy = float(phys.velocity[1])
    vz = float(phys.velocity[2])
    v_ms = math.sqrt(vx * vx + vy * vy + vz * vz)
    return v_ms * 3.6


def _pick_speed_kmh(phys: Any) -> float:
    # (km/h) — Assetto Corsa shared memory
    try:
        sk = float(phys.speedKmh)
    except Exception:
        return 0.0

    sk = abs(sk)

    # sanity check
    if sk > 600:
        return 0.0

    return sk


def to_ssp_frame_ac(
    phys: Any,
    *,
    car_name: Optional[str] = None,
    car_class: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Converte leitura do AC (SPageFilePhysics) para o SSP Frame v0.1.

    Espera que `phys` tenha ao menos:
      - rpms (int)
      - gear (int)
      - gas (float 0..1)
      - brake (float 0..1)
      - speedKmh (float) (opcional se velocity existir)
      - velocity[3] (float*3) (fallback)

    Retorna um dict JSON-serializável.
    """
    rpm = int(getattr(phys, "rpms", 0))
    gear = int(getattr(phys, "gear", 0))

    gas = float(getattr(phys, "gas", 0.0)) * 100.0
    brake = float(getattr(phys, "brake", 0.0)) * 100.0

    speed_kmh = _pick_speed_kmh(phys)

    frame: Dict[str, Any] = {
        "v": "0.1",
        "ts": _now_ts(),
        "source": "ac",
        "signals": {
            "engine.rpm": rpm,
            "vehicle.speed_kmh": speed_kmh,
            "drivetrain.gear": gear,
            "controls.throttle_pct": _clamp_pct(gas),
            "controls.brake_pct": _clamp_pct(brake),
        },
    }

    if car_name or car_class:
        frame["car"] = {}
        if car_name:
            frame["car"]["name"] = car_name
        if car_class:
            frame["car"]["class"] = car_class

    return frame
