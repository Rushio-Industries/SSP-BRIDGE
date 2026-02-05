# SSP Schema v0.2

The **SSP (SimRacing Standard Protocol)** is a universal, simulator-agnostic
telemetry frame format used by **SSP-BRIDGE**.

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
````

---

## Top-level fields

| Field     | Type   | Description                                 |
| --------- | ------ | ------------------------------------------- |
| `v`       | string | Frame format version (`"0.2"`)              |
| `ts`      | number | UNIX timestamp in seconds (float)           |
| `source`  | string | Plugin / simulator ID (`ac`, `acc`, `ams2`) |
| `signals` | object | Flat key-value map of telemetry signals     |

---

## Signals

Rules:

* Flat key-value pairs (no nesting inside `signals`)
* Keys use dot-notation namespaces
* Values are JSON primitives (`number`, `string`, `boolean`)
* **Signals are optional** and MUST be omitted when unavailable
* Missing signals mean *“not available”*, not zero

Naming convention:

```
<domain>.<signal_name>
```

Examples:

* `engine.rpm`
* `vehicle.speed_kmh`
* `drivetrain.gear`
* `controls.throttle_pct`

---

## Units & semantics

Units and signal semantics are **not encoded per frame**.

They are declared via the plugin **capabilities** file to:

* avoid duplication
* reduce frame size
* allow dynamic client adaptation

---

## Core Signals (Frozen)

These signals form the **SSP Core v0.2**.

| Signal                | Type    | Unit |
| --------------------- | ------- | ---- |
| engine.rpm            | integer | rpm  |
| vehicle.speed_kmh     | number  | km/h |
| drivetrain.gear       | integer | gear |
| controls.throttle_pct | number  | %    |
| controls.brake_pct    | number  | %    |

Optional:

* `controls.clutch_pct`

---

## RPM-Derived Signals

Derived from engine telemetry and vehicle metadata.

| Signal         | Type    | Unit      |
| -------------- | ------- | --------- |
| engine.rpm_max | integer | rpm       |
| engine.rpm_pct | number  | 0.0 – 1.0 |

Rules:

* `engine.rpm_max` represents the maximum engine RPM of the current vehicle
* `engine.rpm_pct` is the normalized RPM value:

```
engine.rpm_pct = engine.rpm / engine.rpm_max
```

* `engine.rpm_pct` MUST only be emitted when `engine.rpm_max` is known and valid
* If `engine.rpm_max` is unavailable, both signals MUST be omitted

---

## Vehicle Identification

Optional signal:

* `vehicle.car_id` (string)

Rules:

* Used to identify the current vehicle model when available
* MUST be omitted when unavailable or unstable
* Clients must not assume its presence

---

## Capabilities

Each plugin can export a capabilities file describing:

* Available signals
* Data types
* Units
* Expected update rate (`hz`)
* Optional constraints (`min`, `max`)

Example:

```json
{
  "plugin": "acc",
  "schema": "ssp/0.2",
  "signals": {
    "engine.rpm": {
      "type": "integer",
      "unit": "rpm",
      "hz": 60,
      "min": 0
    },
    "engine.rpm_pct": {
      "type": "number",
      "unit": "ratio",
      "min": 0.0,
      "max": 1.0
    }
  }
}
```

Default output path (CLI `--capabilities auto`):

```
logs/capabilities.<plugin_id>.json
```

---

## Versioning rules

* `v0.x` allows **additive** changes (new signals or metadata)
* Breaking changes require a new major version (`v1.0`)
* Renaming signals or changing semantics is not allowed within the same major version

Compatibility:

* Add signals ✅
* Add metadata ✅
* Rename signals / change meaning ❌

---

SSP is a **contract**, not an implementation detail.
