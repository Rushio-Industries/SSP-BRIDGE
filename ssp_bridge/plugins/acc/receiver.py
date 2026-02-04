from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class LatestPacket:
    data: bytes
    addr: tuple[str, int]
    recv_ts: float
    seq: int


class LatestUDPReceiver:
    """Background UDP receiver that keeps only the newest packet."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, bufsize: int = 4096):
        self._host = host
        self._port = port
        self._bufsize = bufsize

        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self._lock = threading.Lock()
        self._latest: Optional[LatestPacket] = None
        self._seq = 0

    def open(self) -> None:
        if self._sock is not None:
            return
        self._stop.clear()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self._host, self._port))
        sock.settimeout(0.25)

        self._sock = sock
        self._thread = threading.Thread(target=self._run, name="acc-udp-receiver", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

        if self._thread is not None:
            try:
                self._thread.join(timeout=1.0)
            except Exception:
                pass
            self._thread = None

    def _run(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                data, addr = self._sock.recvfrom(self._bufsize)
            except socket.timeout:
                continue
            except OSError:
                break

            now = time.time()
            with self._lock:
                self._seq += 1
                self._latest = LatestPacket(data=data, addr=addr, recv_ts=now, seq=self._seq)

    def get_latest(self) -> Tuple[Optional[bytes], int, float]:
        """
        Returns (data, seq, recv_ts).
        If no packet was ever received: (None, 0, 0.0)
        """
        with self._lock:
            if self._latest is None:
                return None, 0, 0.0
            return self._latest.data, self._latest.seq, self._latest.recv_ts
