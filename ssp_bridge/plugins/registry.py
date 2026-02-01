# ssp_bridge/plugins/registry.py
from __future__ import annotations

from typing import Dict, List, Type

from ssp_bridge.plugins.base import TelemetryPlugin
from ssp_bridge.plugins.ac.plugin import ACPlugin

# ordem importa para --game auto
PLUGIN_ORDER: List[Type[TelemetryPlugin]] = [
    ACPlugin,
]

PLUGINS: Dict[str, Type[TelemetryPlugin]] = {p.id: p for p in PLUGIN_ORDER}


def create_plugin(game_id: str) -> TelemetryPlugin:
    game_id = (game_id or "").strip().lower()
    if game_id not in PLUGINS:
        raise ValueError(f"Unknown game/plugin id: {game_id}. Available: {', '.join(sorted(PLUGINS))}")
    return PLUGINS[game_id]()


def auto_detect_plugin() -> TelemetryPlugin:
    """
    Tries plugins in PLUGIN_ORDER. The first that can open() successfully wins.
    """
    errors = []
    for plugin_cls in PLUGIN_ORDER:
        plugin = plugin_cls()
        try:
            plugin.open()
            return plugin
        except Exception as e:
            errors.append(f"{plugin_cls.id}: {e!r}")
            try:
                plugin.close()
            except Exception:
                pass

    raise RuntimeError("Auto-detect failed. Tried: " + ", ".join(errors))
