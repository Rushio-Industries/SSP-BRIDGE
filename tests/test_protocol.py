import time

def validate_status(ev: dict):
    assert ev.get("type") == "status"
    assert isinstance(ev.get("ts"), (int, float))
    assert ev.get("state") in ("waiting", "active", "lost")
    # source pode ser None ou string curta
    src = ev.get("source")
    assert (src is None) or isinstance(src, str)

def validate_capabilities(ev: dict):
    assert ev.get("type") == "capabilities"
    assert ev.get("schema") == "ssp/0.2"
    assert isinstance(ev.get("ts"), (int, float))
    assert isinstance(ev.get("source"), str)
    caps = ev.get("capabilities")
    assert isinstance(caps, dict)
    assert caps.get("schema") == "ssp/0.2"
    assert isinstance(caps.get("signals"), dict)

def validate_frame(ev: dict):
    assert ev.get("v") == "0.2"
    assert isinstance(ev.get("ts"), (int, float))
    assert isinstance(ev.get("source"), str)
    sig = ev.get("signals")
    assert isinstance(sig, dict)

CORE_SIGNALS = [
    "engine.rpm",
    "vehicle.speed_kmh",
    "drivetrain.gear",
    "controls.throttle_pct",
    "controls.brake_pct",
]

def test_core_signals_declared_in_capabilities():
    # import plugins
    from ssp_bridge.plugins.ac.plugin import ACPlugin
    from ssp_bridge.plugins.acc.plugin import ACCPlugin
    from ssp_bridge.plugins.ams2.plugin import AMS2Plugin

    for cls in (ACPlugin, ACCPlugin, AMS2Plugin):
        p = cls()
        caps = p.capabilities()
        assert caps["schema"] == "ssp/0.2"
        signals = caps["signals"]
        for k in CORE_SIGNALS:
            assert k in signals, f"{cls.__name__} missing core signal: {k}"
            meta = signals[k]
            assert "type" in meta
            assert "unit" in meta
            assert "hz" in meta

def test_frame_shapes_are_valid_when_present():
    # This is a "shape" test, not a runtime integration test.
    now = time.time()
    frame = {
        "v": "0.2",
        "ts": now,
        "source": "ac",
        "signals": {
            "engine.rpm": 1000,
            "vehicle.speed_kmh": 0.0,
            "drivetrain.gear": 1,
            "controls.throttle_pct": 0.0,
            "controls.brake_pct": 0.0,
        },
    }
    validate_frame(frame)

def test_status_and_capabilities_shapes():
    now = time.time()
    status = {"type": "status", "ts": now, "state": "waiting", "source": None}
    validate_status(status)

    caps = {
        "type": "capabilities",
        "ts": now,
        "source": "ac",
        "schema": "ssp/0.2",
        "capabilities": {
            "plugin": "ac",
            "schema": "ssp/0.2",
            "signals": {
                "engine.rpm": {"type": "integer", "unit": "rpm", "hz": 60},
            },
        },
    }
    validate_capabilities(caps)
