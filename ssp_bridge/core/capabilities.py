# ssp_bridge/core/capabilities.py
"""Capability maps and utilities.

Capabilities are emitted on connect/simulator switch so clients can adapt dynamically.
"""

from __future__ import annotations


_BASE_SIGNALS = {
    "engine.rpm": {
        "type": "integer",
        "unit": "rpm",
        "hz": 60,
        "min": 0,
        "max": 25000,
        "precision": 0,
    },

    "engine.rpm_max": {
        "type": "integer",
        "unit": "rpm",
        "hz": 1,
        "min": 0,
        "max": 25000,
        "precision": 0,
        "description": "Maximum engine RPM for current vehicle/session (if available).",
    },

    "engine.rpm_pct": {
    "type": "number",
    "unit": "ratio",
    "hz": 60,
    "min": 0.0,
    "max": 1.0,
    "precision": 3,
    "description": "Engine RPM normalized ratio (engine.rpm / engine.rpm_max), if available.",
    },

    "vehicle.speed_kmh": {
        "type": "number",
        "unit": "km/h",
        "hz": 60,
        "min": 0,
        "max": 600,
        "precision": 1,
    },

    "drivetrain.gear": {
        "type": "integer",
        "unit": "gear",
        "hz": 60,
        "min": -1,
        "max": 10,
        "precision": 0,
    },

    "controls.throttle_pct": {
        "type": "number",
        "unit": "%",
        "hz": 60,
        "min": 0,
        "max": 100,
        "precision": 1,
    },

    "controls.brake_pct": {
        "type": "number",
        "unit": "%",
        "hz": 60,
        "min": 0,
        "max": 100,
        "precision": 1,
    },

    "vehicle.car_id": {
        "type": "string",
        "unit": "",
        "hz": 0,
        "description": "Stable identifier of current vehicle if available.",
    },
}


CAPABILITIES_AC = {
    "plugin": "ac",
    "schema": "ssp/0.2",
    "signals": dict(_BASE_SIGNALS),
}

CAPABILITIES_ACC = {
    "plugin": "acc",
    "schema": "ssp/0.2",
    "signals": dict(_BASE_SIGNALS),
}

CAPABILITIES_AMS2 = {
    "plugin": "ams2",
    "schema": "ssp/0.2",
    "signals": dict(_BASE_SIGNALS),
}

CAPABILITIES_BEAMNG = {
    "plugin": "beamng",
    "schema": "ssp/0.2",
    "signals": dict(_BASE_SIGNALS),
}
