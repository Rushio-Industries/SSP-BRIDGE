# SSP Schema v0.2

The **SSP (SimRacing Standard Protocol)** is a universal, simulator-agnostic telemetry frame format used by **SSP-BRIDGE**.

Goals:

- Simulator-agnostic representation
- Flat, predictable structure
- Easy parsing in any language
- Forward-compatible evolution
- Feature discovery via **capabilities**

---

## Frame structure

Each telemetry frame is a single JSON object.

```json
{
  "v": "0.2",
  "ts": 1769902700.94,
  "source": "ac",
  "signals": {
    "engine.rpm": 3512,
    "vehicle.speed_kmh": 47.5,
    "drivetrain.gear": 3,
    "controls.throttle_pct": 32.4,
    "controls.brake_pct": 0.0
  }
}
```

### Top-level fields

| Field   | Type   | Description |
|--------|--------|-------------|
| `v`     | string | SSP schema version |
| `ts`    | number | UNIX timestamp in seconds (float) |
| `source`| string | Plugin/simulator id (e.g. `ac`, `acc`, `ams2`) |
| `signals` | object | Flat key-value map of telemetry signals |

---

## Signals

Rules:

- Flat key-value pairs (no nesting inside `signals`)
- Keys use dot notation namespaces
- Values are JSON primitives (`number`, `string`, `boolean`)

Naming convention:

```
<domain>.<signal_name>
```

Examples:

- `engine.rpm`
- `vehicle.speed_kmh`
- `drivetrain.gear`
- `controls.throttle_pct`

---

## Units & semantics

Units are **not** encoded in each frame.
They are declared via the plugin **capabilities** file to avoid duplication and allow clients to adapt.

---

## Capabilities

Each plugin can export a capabilities file describing:

- Available signals
- Types
- Units
- Expected update rate (`hz`)

Example:

```json
{
  "plugin": "ac",
  "schema": "ssp/0.2",
  "signals": {
    "engine.rpm": { "type": "integer", "unit": "rpm", "hz": 60 },
    "vehicle.speed_kmh": { "type": "number", "unit": "km/h", "hz": 60 }
  }
}
```

Default output path (CLI `--capabilities auto`):

- `logs/capabilities.<plugin_id>.json`

---

## Versioning rules

- `v0.x` allows **additive** changes (new signals/metadata)
- Breaking changes happen at `v1.0`

Compatibility:

- Add signals ✅
- Add metadata ✅
- Rename signals / change meaning ❌ (within the same major version)
