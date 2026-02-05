# SSP – SimRacing Standard Protocol
Version: ssp/0.2

This document defines the **SSP telemetry protocol**, a simulator-agnostic
data format designed to unify sim racing telemetry for dashboards, tools,
and custom hardware (Arduino, ESP32, etc).

The protocol is **capability-driven**, **state-aware**, and **forward-compatible**.

---

## 1. Core Concepts

### 1.1 State Model

The bridge operates as a persistent state machine and emits lifecycle events:

- `waiting` – No simulator detected
- `active` – Telemetry is flowing
- `lost` – Simulator disconnected or stalled

State events are **deduplicated** and must be handled idempotently by clients.

---

## 2. Message Types

### 2.1 Status Event

```json
{
  "type": "status",
  "ts": 1770225996.75,
  "state": "active",
  "source": "acc"
}
````

| Field  | Type          | Description                 |
| ------ | ------------- | --------------------------- |
| type   | string        | Always `"status"`           |
| ts     | number        | Unix timestamp (seconds)    |
| state  | string        | `waiting`, `active`, `lost` |
| source | string | null | Active simulator or null    |

---

### 2.2 Capabilities Handshake

Emitted on simulator connect or switch.

```json
{
  "type": "capabilities",
  "ts": 1770226017.54,
  "source": "acc",
  "schema": "ssp/0.2",
  "capabilities": {
    "schema": "ssp/0.2",
    "plugin": "acc",
    "signals": {
      "engine.rpm": {
        "type": "integer",
        "unit": "rpm",
        "hz": 60,
        "min": 0,
        "max": 12000
      }
    }
  }
}
```

Capabilities describe **what MAY appear** in telemetry frames.
Signals not listed here must not be assumed by clients.

---

### 2.3 Telemetry Frame

```json
{
  "v": "0.2",
  "ts": 1770226017.57,
  "source": "acc",
  "signals": {
    "engine.rpm": 7200,
    "vehicle.speed_kmh": 145.5
  }
}
```

| Field   | Type   | Description                    |
| ------- | ------ | ------------------------------ |
| v       | string | Frame format version (`"0.2"`) |
| ts      | number | Unix timestamp                 |
| source  | string | Simulator ID                   |
| signals | object | Key-value map of telemetry     |

**Rules:**

* Missing signals mean “not available”, not zero.
* Signals MUST be omitted when unavailable (no null or empty values).
* Clients must rely on capabilities for discovery.
* Backward compatibility is preserved within the same `v`.

---

## 3. Core Signals (Frozen)

These signals form the **SSP Core v0.2**.
Plugins should provide them whenever possible.

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

## 4. RPM-Derived Signals

These signals are derived from core telemetry and vehicle metadata.

| Signal         | Type    | Unit    |
| -------------- | ------- | ------- |
| engine.rpm_max | integer | rpm     |
| engine.rpm_pct | number  | 0.0–1.0 |

**Rules:**

* `engine.rpm_max` represents the maximum engine RPM for the current vehicle.
* `engine.rpm_pct` represents the normalized RPM value (`engine.rpm / engine.rpm_max`).
* `engine.rpm_pct` MUST only be emitted when `engine.rpm_max` is known and valid.
* If `engine.rpm_max` is unavailable, both signals MUST be omitted.

---

## 5. Versioning Rules

* `schema` identifies the SSP generation (`ssp/0.2`).
* `v` identifies the frame format version (`"0.2"`).
* Minor additions do not break clients.
* Renaming signals or changing units requires a new major version.

---

## 6. Design Goals

* Simulator-agnostic
* Hardware-friendly
* No hidden assumptions
* Easy to implement on microcontrollers
* Stable and predictable behavior

---

SSP is a **contract**, not an implementation detail.

