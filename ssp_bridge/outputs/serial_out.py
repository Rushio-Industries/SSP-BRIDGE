# ssp_bridge/outputs/serial_out.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import serial  # pyserial


@dataclass
class SerialOut:
    """
    Serial NDJSON output.

    Sends one line per frame over a serial port (USB),
    designed for Arduino / ESP32 / microcontrollers.

    The class is intentionally simple:
    - no parsing
    - no buffering logic
    - no simulator-specific behavior
    """

    port: str
    baud: int = 115200
    enabled: bool = True
    rate_hz: int = 60  # Maximum lines per second (protects microcontrollers)

    def __post_init__(self) -> None:
        self._ser: Optional[serial.Serial] = None
        self._next_send_ts: float = 0.0

        if not self.enabled:
            return

        try:
            # Non-blocking serial connection
            self._ser = serial.Serial(
                self.port,
                self.baud,
                timeout=0,
                write_timeout=0.05,
            )
        except Exception as exc:
            # Serial is optional: failure must not crash the bridge
            print(f"[SerialOut] Failed to open serial port {self.port}: {exc}")
            self.enabled = False

    def _rate_limit_ok(self) -> bool:
        """
        Simple rate limiter.

        Prevents flooding slow devices like Arduino.
        """
        if self.rate_hz <= 0:
            return True

        now = time.time()
        if now < self._next_send_ts:
            return False

        self._next_send_ts = now + (1.0 / self.rate_hz)
        return True

    def send_line(self, line: str) -> None:
        """
        Sends a single line over serial.

        The caller is responsible for formatting (NDJSON).
        """
        if not self.enabled or not self._ser:
            return

        if not self._rate_limit_ok():
            return

        try:
            self._ser.write((line + "\n").encode("utf-8", errors="ignore"))
        except Exception:
            # Never crash the application because of serial errors
            pass

    def close(self) -> None:
        """
        Closes the serial port safely.
        """
        if not self._ser:
            return

        try:
            self._ser.close()
        except Exception:
            pass
        finally:
            self._ser = None
