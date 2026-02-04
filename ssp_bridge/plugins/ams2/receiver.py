"""UDP receiver for SMS/AMS2 telemetry.

Keeps the latest valid packet so callers can poll without blocking."""
# ssp_bridge/plugins/ams2/receiver.py
from __future__ import annotations

import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Optional


# PacketBase (12 bytes):
# uint32 mPacketNumber
# uint32 mCategoryPacketNumber
# uint8  mPartialPacketIndex
# uint8  mPartialPacketNumber
# uint8  mPacketType
# uint8  mPacketVersion
_PACKET_BASE_FMT = "<II4B"
_PACKET_BASE_SIZE = 12

# eCarPhysics (Telemetry) = packetType 0 (SMS UDP)
_PACKET_TYPE_CAR_PHYSICS = 0

# sTelemetryData size in the Patch5 header:
# static const unsigned int sPacketSize = 559;
_TELEMETRY_PACKET_SIZE = 559

# Offsets (bytes) inside sTelemetryData (Patch5)
# (ver SMS_UDP_Definitions.hpp)
_OFF_BRAKE = 29          # uint8
_OFF_THROTTLE = 30       # uint8
_OFF_SPEED = 36          # float
_OFF_RPM = 40            # uint16
_OFF_GEAR_NUM_GEARS = 45 # uint8


def _now_ts() -> float:
    return time.time()


def _u8_to_pct(x: int) -> float:
    # 0..255 -> 0..100
    if x < 0:
        x = 0
    if x > 255:
        x = 255
    return (x / 255.0) * 100.0


def _decode_gear(gear_num_gears: int) -> tuple[int, int]:
    """
    sGearNumGears is a uint8 that is typically bit-packed.
    Common (SMS/PCARS) encoding: low nibble = gear, high nibble = num gears.
    - gear 0 => N
    - gear 15 => R (sentinela comum)
    """
    gear_raw = gear_num_gears & 0x0F
    num_gears = (gear_num_gears >> 4) & 0x0F

    if gear_raw == 0:
        gear = 0
    elif gear_raw == 15:
        gear = -1
    else:
        gear = int(gear_raw)

    return gear, int(num_gears)


@dataclass(frozen=True)
class AMS2Telemetry:
    ts: float
    rpm: int
    speed_ms: float
    throttle_pct: float
    brake_pct: float
    gear: int
    num_gears: int


class LatestUDPReceiver:
    """
    Simple receiver: always keeps the latest valid eCarPhysics packet.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 5606) -> None:
        self._host = host
        self._port = int(port)

        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self._lock = threading.Lock()
        self._latest: Optional[AMS2Telemetry] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self._host, self._port))
        # timeout pequeno pra conseguir parar limpo
        self._sock.settimeout(0.2)

        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="ams2-udp-receiver", daemon=True)
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

    def get_latest(self) -> Optional[AMS2Telemetry]:
        with self._lock:
            return self._latest

    def _run(self) -> None:
        assert self._sock is not None

        while not self._stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break

            if len(data) < _PACKET_BASE_SIZE:
                continue

            # Lê PacketBase
            try:
                mPacketNumber, mCategoryPacketNumber, mPartialPacketIndex, mPartialPacketNumber, mPacketType, mPacketVersion = struct.unpack_from(
                    _PACKET_BASE_FMT, data, 0
                )
            except struct.error:
                continue

            if mPacketType != _PACKET_TYPE_CAR_PHYSICS:
                continue

            # Require a minimum size to read the fields we use.
            # (Patch5 header states 559 bytes for sTelemetryData).
            if len(data) < _TELEMETRY_PACKET_SIZE:
                # Some setups may send larger/smaller packets; if offsets are missing, ignore.
                if len(data) < (_OFF_GEAR_NUM_GEARS + 1):
                    continue

            try:
                brake_u8 = struct.unpack_from("<B", data, _OFF_BRAKE)[0]
                throttle_u8 = struct.unpack_from("<B", data, _OFF_THROTTLE)[0]
                speed_ms = struct.unpack_from("<f", data, _OFF_SPEED)[0]
                rpm = struct.unpack_from("<H", data, _OFF_RPM)[0]
                gear_num_gears = struct.unpack_from("<B", data, _OFF_GEAR_NUM_GEARS)[0]
            except struct.error:
                continue

            gear, num_gears = _decode_gear(gear_num_gears)

            tel = AMS2Telemetry(
                ts=_now_ts(),
                rpm=int(rpm),
                speed_ms=float(speed_ms),
                throttle_pct=_u8_to_pct(int(throttle_u8)),
                brake_pct=_u8_to_pct(int(brake_u8)),
                gear=int(gear),
                num_gears=int(num_gears),
            )

            with self._lock:
                self._latest = tel