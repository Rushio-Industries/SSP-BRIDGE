"""Capability maps and utilities.

Capabilities are emitted on connect/simulator switch so clients can adapt dynamically."""
from __future__ import annotations

# Centralized capabilities definitions (used by plugins and for exporting JSON files).
# Keep these consistent across plugins so downstream tools can rely on one format.

CAPABILITIES_AC = {
  "plugin": "ac",
  "schema": "ssp/0.2",
  "signals": {
    "engine.rpm": {"type": "integer", "unit": "rpm", "hz": 60},
    "vehicle.speed_kmh": {"type": "number", "unit": "km/h", "hz": 60},
    "drivetrain.gear": {"type": "integer", "unit": "gear", "hz": 60},
    "controls.throttle_pct": {"type": "number", "unit": "%", "hz": 60},
    "controls.brake_pct": {"type": "number", "unit": "%", "hz": 60},
  }
}

CAPABILITIES_ACC = {
  "plugin": "acc",
  "schema": "ssp/0.2",
  "signals": {
    "engine.rpm": {"type": "integer", "unit": "rpm", "hz": 60},
    "vehicle.speed_kmh": {"type": "number", "unit": "km/h", "hz": 60},
    "drivetrain.gear": {"type": "integer", "unit": "gear", "hz": 60},
    "controls.throttle_pct": {"type": "number", "unit": "%", "hz": 60},
    "controls.brake_pct": {"type": "number", "unit": "%", "hz": 60},
  }
}

CAPABILITIES_AMS2 = {
  "plugin": "ams2",
  "schema": "ssp/0.2",
  "signals": {
    "engine.rpm": {"type": "integer", "unit": "rpm", "hz": 60},
    "vehicle.speed_kmh": {"type": "number", "unit": "km/h", "hz": 60},
    "drivetrain.gear": {"type": "integer", "unit": "gear", "hz": 60},
    "controls.throttle_pct": {"type": "number", "unit": "%", "hz": 60},
    "controls.brake_pct": {"type": "number", "unit": "%", "hz": 60},
  }
}