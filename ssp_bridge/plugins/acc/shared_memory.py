"""ACC shared memory reader.

Wraps the ACC shared memory structures (Windows)."""
import ctypes
from ctypes import wintypes
import struct
import time
from typing import Optional


ACC_PHYSICS_MAP = r"Local\acpmf_physics"
ACC_STATIC_MAP = r"Local\acpmf_static"

FILE_MAP_READ = 0x0004

# ACC shared memory reader is Windows-only (uses WinAPI mappings).
# Keep module importable on non-Windows so the package can still be imported/docs built.
import sys

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
    k32 = None

    def _win_only(*_args, **_kwargs):
        raise RuntimeError("ACC shared memory is only available on Windows.")

    OpenFileMappingW = _win_only
    MapViewOfFile = _win_only
    UnmapViewOfFile = _win_only
    CloseHandle = _win_only


# ---- Offsets (ACC PHYSICS) ----
OFF_PACKET = 0

# Pedals (your finder results)
OFF_THROTTLE = 4   # float32 0..1
OFF_BRAKE = 8      # float32 0..1

# Core signals
OFF_GEAR = 16      # int32
OFF_RPM = 20       # int32
OFF_SPEED = 28     # float32 km/h (you confirmed)

READ_PREFIX = 256

class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion", ctypes.c_wchar * 15),
        ("acVersion", ctypes.c_wchar * 15),
        ("numberOfSessions", ctypes.c_int),
        ("numCars", ctypes.c_int),
        ("carModel", ctypes.c_wchar * 33),
        ("track", ctypes.c_wchar * 33),
        ("playerName", ctypes.c_wchar * 33),
        ("playerSurname", ctypes.c_wchar * 33),
        ("playerNick", ctypes.c_wchar * 33),
        ("sectorCount", ctypes.c_int),
        ("maxTorque", ctypes.c_float),
        ("maxPower", ctypes.c_float),
        ("maxRpm", ctypes.c_int),
    ]

class ACCSharedMemory:
    """
    ACC telemetry reader using WinAPI mapping (read-only) + offset unpacking.

    Outputs:
      - engine.rpm (int)
      - vehicle.speed_kmh (float)
      - drivetrain.gear (int)
      - controls.throttle_pct (float 0..100)
      - controls.brake_pct (float 0..100)

    Notes:
      - No clutch (by design for now).
      - If mapping becomes stale, raises RuntimeError so app.py can reopen cleanly.
    """

    def __init__(self):
        self._hmap: Optional[int] = None
        self._hmap_static: Optional[int] = None
        self._view_static: Optional[int] = None

        self._static_last_read_ts: float = 0.0
        self._car_model: str = ""
        self._max_rpm: int = 0
        self._view: Optional[int] = None

        self._last_pkt: Optional[int] = None
        self._last_pkt_change_ts: float = 0.0

        self.debug = False
        self._last_dbg_ts = 0.0


    def open(self):
        hmap = OpenFileMappingW(FILE_MAP_READ, False, ACC_PHYSICS_MAP)
        if not hmap:
            raise RuntimeError("ACC shared memory not available yet (mapping not created).")
        
        # Open STATIC mapping (carModel/maxRpm)
        hmap_s = OpenFileMappingW(FILE_MAP_READ, False, ACC_STATIC_MAP)
        if hmap_s:
            view_s = MapViewOfFile(hmap_s, FILE_MAP_READ, 0, 0, 0)
            if view_s:
                self._hmap_static = int(hmap_s)
                self._view_static = int(view_s)
            else:
                CloseHandle(hmap_s)
                self._hmap_static = None
                self._view_static = None
        else:
            self._hmap_static = None
            self._view_static = None

        view = MapViewOfFile(hmap, FILE_MAP_READ, 0, 0, 0)
        if not view:
            CloseHandle(hmap)
            raise RuntimeError("MapViewOfFile failed for ACC physics mapping.")

        self._hmap = int(hmap)
        self._view = int(view)

        now = time.time()
        self._last_pkt = None
        self._last_pkt_change_ts = now

    def close(self):
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
        if self._view_static is not None:
            try:
                UnmapViewOfFile(self._view_static)
            finally:
                self._view_static = None

        if self._hmap_static is not None:
            try:
                CloseHandle(self._hmap_static)
            finally:
                self._hmap_static = None

        self._car_model = ""
        self._max_rpm = 0
        self._static_last_read_ts = 0.0        

        self._last_pkt = None
        self._last_pkt_change_ts = 0.0

    def read(self):
        if self._view is None:
            return None

        raw = ctypes.string_at(self._view, READ_PREFIX)

        pkt = struct.unpack_from("<i", raw, OFF_PACKET)[0]
        throttle = struct.unpack_from("<f", raw, OFF_THROTTLE)[0]
        brake = struct.unpack_from("<f", raw, OFF_BRAKE)[0]

        gear = struct.unpack_from("<i", raw, OFF_GEAR)[0]
        rpm = struct.unpack_from("<i", raw, OFF_RPM)[0]
        speed = struct.unpack_from("<f", raw, OFF_SPEED)[0]

        now = time.time()

        self._read_static_cached(now)

        # Stale detection hint (packetId should normally advance during active sessions).
        if self._last_pkt is None:
            self._last_pkt = pkt
            self._last_pkt_change_ts = now
        elif pkt != self._last_pkt:
            self._last_pkt = pkt
            self._last_pkt_change_ts = now

        if self.debug and (now - self._last_dbg_ts) > 1.0:
            self._last_dbg_ts = now
            print(
                f"ACC DBG pkt={pkt} rpm={rpm} speed={speed:.2f} gear={gear} "
                f"thr={throttle:.3f} brk={brake:.3f}"
            )

        if not self._plausible(pkt, rpm, speed, gear, throttle, brake):
            # if stuck for a while, return None (don't force reopen; ACC can have stale packets in menu/pause)
            if (now - self._last_pkt_change_ts) > 6.0:
                return None
            return None

        rpm_max = self._max_rpm or 0
        rpm_pct = 0.0
        if rpm_max > 0:
            rpm_pct = max(0.0, min(100.0, (float(rpm) / float(rpm_max)) * 100.0))

        sig = {
            "engine.rpm": int(rpm),
            "vehicle.speed_kmh": float(speed),
            "drivetrain.gear": int(gear),
            "controls.throttle_pct": self._clamp01(throttle) * 100.0,
            "controls.brake_pct": self._clamp01(brake) * 100.0,
        }

        car_id = self._car_model or ""
        if car_id:
            sig["vehicle.car_id"] = car_id

        if rpm_max > 0:
            sig["engine.rpm_max"] = int(rpm_max)
            sig["engine.rpm_pct"] = float(round(rpm_pct, 1))

        return {"v": "0.2", "ts": now, "source": "acc", "signals": sig}

    def _clamp01(self, x: float) -> float:
        if x < 0.0:
            return 0.0
        if x > 1.0:
            return 1.0
        return x

    def _plausible(self, pkt: int, rpm: int, speed: float, gear: int, thr: float, brk: float) -> bool:
        if pkt <= 0:
            return False

        if rpm < 0 or rpm > 25000:
            return False

        if speed < -10.0 or speed > 700.0:
            return False

        if gear < -1 or gear > 10:
            return False

        # pedal sanity (allow tiny noise)
        if thr < -0.10 or thr > 1.10:
            return False
        if brk < -0.10 or brk > 1.10:
            return False

        # valid if engine alive OR moving OR pressing pedals
        if rpm > 200 or abs(speed) > 1.0 or thr > 0.05 or brk > 0.05:
            return True

        return False
    def _read_static_cached(self, now: float) -> None:
        if self._view_static is None:
            return

        # evita ler o tempo todo, mas acelera quando max_rpm está zerado (troca de carro)
        interval = 0.15 if self._max_rpm == 0 else 0.5
        if (now - self._static_last_read_ts) < interval:
            return

        self._static_last_read_ts = now

        try:
            s = SPageFileStatic.from_address(self._view_static)
            car_model = (s.carModel or "").strip("\x00").strip()
            max_rpm = int(s.maxRpm)

            # Se trocar de carro, reseta max rpm imediatamente
            if car_model and car_model != self._car_model:
                self._car_model = car_model
                self._max_rpm = 0  # força recalcular no próximo read

            # Atualiza max rpm quando vier plausível
            if 1000 <= max_rpm <= 25000:
                self._max_rpm = max_rpm
        except Exception:
            # se der ruim, só ignora (não derruba o runtime)
            return