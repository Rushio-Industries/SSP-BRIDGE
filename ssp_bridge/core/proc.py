"""Process detection utilities.

Used by auto-detect to prioritize running simulators without expensive per-frame calls."""
# ssp_bridge/core/proc.py
from __future__ import annotations

import sys
import time
import subprocess
from dataclasses import dataclass


@dataclass
class ProcessWatch:
    image_name: str
    cache_ttl: float = 0.75       # check at most once per 750ms
    miss_threshold: int = 3       # require 3 consecutive misses to report "not running"
    _last_check_ts: float = 0.0
    _cached_running: bool = True
    _misses: int = 0

    def reset(self) -> None:
        self._last_check_ts = 0.0
        self._cached_running = True
        self._misses = 0

    def running(self) -> bool:
        if sys.platform != "win32":
            return True

        now = time.time()
        if (now - self._last_check_ts) < self.cache_ttl:
            return self._cached_running

        self._last_check_ts = now

        # If tasklist fails, assume "running" (do not crash due to system instability).
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {self.image_name}", "/FO", "CSV", "/NH"],
                text=True,
                encoding="utf-8",
                errors="ignore",
            ).strip().lower()
        except Exception:
            self._cached_running = True
            self._misses = 0
            return True

        found = (self.image_name.lower() in out) and ("no tasks" not in out)

        if found:
            self._cached_running = True
            self._misses = 0
            return True

        # Not found this time: count a miss.
        self._misses += 1
        if self._misses >= self.miss_threshold:
            self._cached_running = False
            return False

        # Below miss threshold: keep "running" to avoid status flapping.
        self._cached_running = True
        return True