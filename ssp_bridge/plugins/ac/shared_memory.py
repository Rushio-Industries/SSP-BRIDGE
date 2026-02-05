"""AC shared memory reader (Windows).

Uses WinAPI file mapping to read Assetto Corsa shared memory.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import struct
import time
from typing import Optional
import sys

FILE_MAP_READ = 0x0004

# AC physics mapping names. Some systems expose without "Local\".
AC_PHYSICS_MAP_CANDIDATES = [
    r"Local\acpmf_physics",
    r"acpmf_physics",
]

# Offsets based on common SPageFilePhysics layout:
# int32 packetId
# float gas
# float brake
# float fuel
# int32 gear
# int32 rpms
# float steerAngle
# float speedKmh
OFF_PACKET = 0
OFF_GAS = 4
OFF_BRAKE = 8
OFF_GEAR = 16
OFF_RPM = 20
OFF_SPEED = 28

READ_PREFIX = 128


if sys.platform == "win32":
    k32 = ctypes.windll.kernel32

    OpenFileMappingW = k32.OpenFileMappingW
    OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    OpenFileMappingW.restype = wintypes.HANDLE

    MapViewOfFile = k32.MapViewOfFile
    MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
    MapViewOfFile.restype = wintypes.LPVOID

    UnmapViewOfFile = k32.UnmapViewOfFile
    UnmapViewOfFile.argtypes = [wintypes.LPCVOID]
    UnmapViewOfFile.restype = wintypes.BOOL

    CloseHandle = k32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL
else:
    def _win_only(*_args, **_kwargs):
        raise RuntimeError("AC shared memory is only available on Windows.")

    OpenFileMappingW = _win_only
    MapViewOfFile = _win_only
    UnmapViewOfFile = _win_only
    CloseHandle = _win_only


class ACSharedMemory:
    """Read-only AC physics mapping reader."""

    def __init__(self) -> None:
        self._hmap: Optional[int] = None
        self._view: Optional[int] = None

        # Derived (bridge-estimated) rpm_max when sim doesn't provide it
        self._rpm_max_obs: int = 0
        self._low_rpm_since: float = 0.0

    def open(self) -> None:
        hmap = None
        for name in AC_PHYSICS_MAP_CANDIDATES:
            hm = OpenFileMappingW(FILE_MAP_READ, False, name)
            if hm:
                hmap = hm
                break

        if not hmap:
            raise RuntimeError("AC shared memory not available yet (mapping not created).")

        view = MapViewOfFile(hmap, FILE_MAP_READ, 0, 0, 0)
        if not view:
            CloseHandle(hmap)
            raise RuntimeError("MapViewOfFile failed for AC physics mapping.")

        self._hmap = int(hmap)
        self._view = int(view)

        self._rpm_max_obs = 0
        self._low_rpm_since = 0.0

    def close(self) -> None:
        if self._view is not None:
            try:
                UnmapViewOfFile(self._view)
            finally:
                self._view = None

        if self._hmap is not None:
            try:
                CloseHandle(self._hmap)
            finally:
                self._hmap = None

        self._rpm_max_obs = 0
        self._low_rpm_since = 0.0

    def read(self):
        if self._view is None:
            return None

        raw = ctypes.string_at(self._view, READ_PREFIX)

        try:
            pkt = struct.unpack_from("<i", raw, OFF_PACKET)[0]
            gas = struct.unpack_from("<f", raw, OFF_GAS)[0]
            brake = struct.unpack_from("<f", raw, OFF_BRAKE)[0]
            gear = struct.unpack_from("<i", raw, OFF_GEAR)[0]
            rpm = struct.unpack_from("<i", raw, OFF_RPM)[0]
            speed = struct.unpack_from("<f", raw, OFF_SPEED)[0]
        except struct.error:
            return None

        now = time.time()

        if not self._plausible(pkt, rpm, speed, gear, gas, brake):
            return None

        # Derived rpm_max (observed) + reset heuristic
        # Reset if RPM stays very low for a bit (new session/car/menu transitions)
        if rpm < 500:
            if self._low_rpm_since <= 0.0:
                self._low_rpm_since = now
            elif (now - self._low_rpm_since) > 2.5:
                self._rpm_max_obs = 0
        else:
            self._low_rpm_since = 0.0
            if rpm > self._rpm_max_obs:
                self._rpm_max_obs = int(rpm)

        rpm_max = int(self._rpm_max_obs) if self._rpm_max_obs > 0 else 0
        rpm_pct = 0.0
        if rpm_max > 0:
            rpm_pct = max(0.0, min(100.0, (float(rpm) / float(rpm_max)) * 100.0))

        return {
            "v": "0.2",
            "ts": now,
            "source": "ac",
            "signals": {
                "engine.rpm": int(rpm),
                "vehicle.speed_kmh": float(speed),
                "drivetrain.gear": int(gear),
                "controls.throttle_pct": self._clamp01(gas) * 100.0,
                "controls.brake_pct": self._clamp01(brake) * 100.0,
                # unified extras
                "engine.rpm_max": int(rpm_max),
                "engine.rpm_pct": float(round(rpm_pct, 1)),
                "vehicle.car_id": "",  # AC: not available (keep stable key)
            },
        }

    def _clamp01(self, x: float) -> float:
        if x < 0.0:
            return 0.0
        if x > 1.0:
            return 1.0
        return x

    def _plausible(self, pkt: int, rpm: int, speed: float, gear: int, gas: float, brake: float) -> bool:
        if pkt <= 0:
            return False
        if rpm < 0 or rpm > 25000:
            return False
        if speed < -10.0 or speed > 700.0:
            return False
        if gear < -1 or gear > 10:
            return False
        if gas < -0.10 or gas > 1.10:
            return False
        if brake < -0.10 or brake > 1.10:
            return False

        # Consider valid if engine alive OR moving OR pedals
        if rpm > 200 or abs(speed) > 1.0 or gas > 0.05 or brake > 0.05:
            return True

        return False
