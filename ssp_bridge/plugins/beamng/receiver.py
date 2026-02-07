"""UDP receiver for BeamNG OutGauge.

Keeps the latest valid packet so callers can poll without blocking.

BeamNG OutGauge format follows the Live For Speed OutGauge packet layout.
BeamNG docs: Protocols > OutGauge UDP protocol.
"""
from __future__ import annotations

import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Optional


# BeamNG OutGauge packet format (little-endian):
# typedef struct {
#   unsigned       time;        // ms (BeamNG: hardcoded 0)
#   char           car[4];      // (BeamNG: "beam")
#   unsigned short flags;
#   char           gear;        // Reverse:0, Neutral:1, First:2...
#   char           plid;        // (BeamNG: hardcoded 0)
#   float          speed;       // m/s
#   float          rpm;         // rpm
#   float          turbo;       // bar
#   float          engTemp;     // C
#   float          fuel;        // 0..1
#   float          oilPressure; // bar (BeamNG: hardcoded 0)
#   float          oilTemp;     // C
#   unsigned       dashLights;
#   unsigned       showLights;
#   float          throttle;    // 0..1
#   float          brake;       // 0..1
#   float          clutch;      // 0..1
#   char           display1[16];
#   char           display2[16];
#   int            id;          // optional if OutGauge ID is specified
# } OutGauge;
#
# Source: BeamNG docs.
_OG_FMT = "<I4sHcc7fII3f16s16si"
_OG_SIZE = struct.calcsize(_OG_FMT)


def _now_ts() -> float:
    return time.time()


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _ratio_to_pct(x: float) -> float:
    return _clamp01(float(x)) * 100.0


def _gear_to_ssp(gear_raw: int) -> int:
    """
    BeamNG OutGauge: Reverse=0, Neutral=1, First=2...
    SSP: -1=reverse, 0=neutral, 1=first...
    """
    if gear_raw <= 0:
        return -1
    return int(gear_raw) - 1


@dataclass(frozen=True)
class BeamNGTelemetry:
    ts: float
    rpm: int
    speed_ms: float
    throttle_pct: float
    brake_pct: float
    gear: int



class LatestOutGaugeReceiver:
    """Simple receiver that keeps the latest valid OutGauge packet."""

    def __init__(self, host: str = "0.0.0.0", port: int = 4444) -> None:
        self._host = host
        self._port = int(port)

        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self._lock = threading.Lock()
        self._latest: Optional[BeamNGTelemetry] = None
        self._last_error: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._last_error = None

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self._host, self._port))
            self._sock.settimeout(0.2)  # short timeout so we can stop cleanly
        except Exception as exc:
            self._last_error = f"Failed to bind UDP {self._host}:{self._port} ({exc})"
            # Do not crash the whole bridge; receiver just won't run.
            self._sock = None
            return

        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="beamng-outgauge-receiver", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None
        self._thread = None

    def last_error(self) -> str | None:
        return self._last_error

    def get_latest(self) -> Optional[BeamNGTelemetry]:
        with self._lock:
            return self._latest

    def _run(self) -> None:
        if self._sock is None:
            return

        while not self._stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break

            if len(data) < _OG_SIZE:
                continue

            try:
                (
                    _time_ms,
                    car4,
                    _flags,
                    gear_c,
                    _plid_c,
                    speed_ms,
                    rpm,
                    _turbo,
                    _eng_temp,
                    _fuel,
                    _oil_pressure,
                    _oil_temp,
                    _dash_lights,
                    _show_lights,
                    throttle,
                    brake,
                    _clutch,
                    _disp1,
                    _disp2,
                    _id,
                ) = struct.unpack_from(_OG_FMT, data, 0)
            except struct.error:
                continue

            # Optional: ignore non-BeamNG packets (best effort)
            # BeamNG commonly sends b"beam" here.
            if car4 not in (b"beam", b"BEAM"):
                # If you ever find this blocks your data, you can remove this check.
                continue

            # gear byte: be tolerant (signed/unsigned)
            gear_raw = int.from_bytes(gear_c, byteorder="little", signed=True)
            if gear_raw < 0:
                # Some sources may send -1 for reverse; normalize to 0 as "reverse raw"
                gear_raw = 0

            tel = BeamNGTelemetry(
                ts=_now_ts(),
                rpm=int(rpm) if rpm >= 0 else 0,
                speed_ms=float(speed_ms),
                throttle_pct=_ratio_to_pct(float(throttle)),
                brake_pct=_ratio_to_pct(float(brake)),
                gear=_gear_to_ssp(int(gear_raw)),
            )

            with self._lock:
                self._latest = tel

            try:
                (
                    _time_ms,
                    _car4,
                    _flags,
                    gear_c,
                    _plid_c,
                    speed_ms,
                    rpm,
                    _turbo,
                    _eng_temp,
                    _fuel,
                    _oil_pressure,
                    _oil_temp,
                    _dash_lights,
                    _show_lights,
                    throttle,
                    brake,
                    _clutch,
                    _disp1,
                    _disp2,
                    _id,
                ) = struct.unpack_from(_OG_FMT, data, 0)
            except struct.error:
                continue

            # gear_c is a 1-byte "char" -> bytes length 1
            gear_raw = int.from_bytes(gear_c, byteorder="little", signed=False)

            tel = BeamNGTelemetry(
                ts=_now_ts(),
                rpm=int(rpm) if rpm >= 0 else 0,
                speed_ms=float(speed_ms),
                throttle_pct=_ratio_to_pct(float(throttle)),
                brake_pct=_ratio_to_pct(float(brake)),
                gear=_gear_to_ssp(gear_raw),
            )

            with self._lock:
                self._latest = tel
