"""Assetto Corsa shared memory reader.

Thin ctypes wrapper over the AC shared memory layout."""
import mmap
import ctypes

class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
    ]


class ACPhysicsView:
    def __init__(self):
        self._size = ctypes.sizeof(SPageFilePhysics)
        # Must be writable for ctypes.from_buffer().
        self._mm = mmap.mmap(-1, self._size, tagname="acpmf_physics", access=mmap.ACCESS_WRITE)
        self.data = SPageFilePhysics.from_buffer(self._mm)

    def close(self):
        try:
            self._mm.close()
        except Exception:
            pass