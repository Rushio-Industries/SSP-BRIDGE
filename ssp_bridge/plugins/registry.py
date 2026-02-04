"""Plugin registry and auto-detection.

Auto mode is conservative: a plugin becomes active only after producing real telemetry frames."""
# ssp_bridge/plugins/registry.py
from __future__ import annotations

import time
from typing import Dict, List, Type
import sys
import subprocess


from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.plugins.ac.plugin import ACPlugin
from ssp_bridge.plugins.acc.plugin import ACCPlugin
from ssp_bridge.plugins.ams2.plugin import AMS2Plugin

# Notes:
# - AC shared memory mapping can be created even when the game is not running
#   (mmap with a tagname will happily create a new mapping).
# - ACC uses a WinAPI mapping that only exists when the game creates it.
# This is why `--game auto` behave correctly, we try ACC first, then AC.
PLUGIN_ORDER: List[Type[TelemetryPlugin]] = [
    
    ACCPlugin,
    AMS2Plugin,
    ACPlugin,
]

PLUGINS: Dict[str, Type[TelemetryPlugin]] = {p.id: p for p in PLUGIN_ORDER}

def _tasklist_image_names() -> set[str]:
    """
    Returns a set of running process image names (lowercase) on Windows.
    On non-Windows, returns empty set.
    """
    if sys.platform != "win32":
        return set()

    try:
        out = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return set()

    names = set()
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # CSV: "Image Name","PID","Session Name","Session#","Mem Usage"
        # We only need the first field
        if line.startswith('"'):
            parts = line.split('","')
            if parts:
                img = parts[0].strip('"').lower()
                names.add(img)
        else:
            # fallback (rare)
            img = line.split()[0].lower()
            names.add(img)

    return names


def _prefer_assetto_plugin_order(default_order: list[type]) -> list[type]:
    """
    If we can tell AC vs ACC by running processes, reorder probe priority accordingly.
    """
    procs = _tasklist_image_names()

    # Known executables:
    # ACC: AC2-Win64-Shipping.exe
    # AC:  acs.exe  (Content Manager / AC itself)
    is_acc = "ac2-win64-shipping.exe" in procs
    is_ac = "acs.exe" in procs or "assettocorsa.exe" in procs

    if not (is_acc or is_ac):
        return default_order

    # If ACC process is running, prefer ACC first.
    # If AC process is running (and not ACC), prefer AC first.
    reordered = list(default_order)

    def move_front(cls_name: str):
        nonlocal reordered
        for i, c in enumerate(reordered):
            if c.__name__ == cls_name:
                reordered.insert(0, reordered.pop(i))
                return

    if is_acc:
        move_front("ACCPlugin")
    elif is_ac:
        move_front("ACPlugin")

    return reordered


def create_plugin(game_id: str) -> TelemetryPlugin:
    game_id = (game_id or "").strip().lower()
    if game_id not in PLUGINS:
        raise ValueError(f"Unknown game/plugin id: {game_id}. Available: {', '.join(sorted(PLUGINS))}")
    return PLUGINS[game_id]()


def auto_detect_plugin(probe_timeout: float = 0.8, probe_interval: float = 0.02) -> TelemetryPlugin:
    """
    Try plugins in order. A plugin only "wins" if it produces at least one
    real telemetry frame within probe_timeout.
    """
    errors = []

    order = _prefer_assetto_plugin_order(list(PLUGIN_ORDER))
    # Process cache (avoids calling tasklist in a tight loop).
    procs = _tasklist_image_names()
    
    for plugin_cls in order:
        plugin = plugin_cls()
        try:
            plugin.open()

            # Heuristic: if the simulator process is running,
            # do not require an immediate telemetry frame during probing.
            # (ACC/AC may sit in menus/loading and not update telemetry for a few seconds).
            if sys.platform == "win32":
                if getattr(plugin, "id", None) == "acc" and "ac2-win64-shipping.exe" in procs:
                    return plugin
                if getattr(plugin, "id", None) == "ac" and (
                    "acs.exe" in procs or "assettocorsa.exe" in procs
                ):
                    return plugin

            deadline = time.time() + float(probe_timeout)
            while time.time() < deadline:
                frame = plugin.read_frame()
                if frame is not None:
                    return plugin
                time.sleep(float(probe_interval))

            raise RuntimeError("opened but no live telemetry frames during probe")

        except Exception as e:
            errors.append(f"{plugin_cls.__name__}: {e!r}")
            try:
                plugin.close()
            except Exception:
                pass

    raise RuntimeError("Auto-detect failed. Tried: " + ", ".join(errors))