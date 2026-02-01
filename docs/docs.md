# SSP Schema v0.2

The **SSP (SimRacing Standard Protocol)** defines a universal, simulator-agnostic
telemetry frame format used by **SSP-BRIDGE**.

Its goal is to provide a **stable, extensible, and easy-to-consume telemetry contract**
for dashboards, tools, analytics, and future hardware integrations.

---

## 🎯 Design Goals

- Simulator-agnostic telemetry representation
- Flat, predictable data structure
- Easy parsing in any language
- Forward-compatible schema evolution
- Explicit feature discovery via capabilities

---

## 📐 Frame Structure

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
🧱 Top-Level Fields
Field	Type	Description
v	string	SSP schema version
ts	number	UNIX timestamp (seconds, float)
source	string	Simulator or plugin identifier (e.g. ac)
signals	object	Flat key-value map of telemetry signals
🔑 Signals
General Rules
Signals are flat key-value pairs

Keys are namespaced using dot notation

Values must be JSON-serializable primitives (number, boolean, string)

Naming Convention
<domain>.<signal_name>
Examples:

engine.rpm

vehicle.speed_kmh

drivetrain.gear

controls.throttle_pct

📊 Units & Semantics
Units are not encoded in the frame itself.
They are declared via the capabilities file exposed by SSP-BRIDGE.

This avoids duplication and allows tools to adapt dynamically.

🔍 Feature Discovery (Capabilities)
Each plugin exposes a capabilities description file that defines:

Available signals

Units

Expected update rate

Data types

Optional metadata

Example Capabilities File
{
  "schema": "ssp/0.2",
  "source": "ac",
  "signals": {
    "engine.rpm": {
      "unit": "rpm",
      "type": "int",
      "hz": 60
    },
    "vehicle.speed_kmh": {
      "unit": "km/h",
      "type": "float",
      "hz": 60
    }
  }
}
Purpose
Enables auto-configuring dashboards

Prevents hardcoded simulator assumptions

Allows graceful degradation when signals are unavailable

🔄 Schema Versioning
Schema versions follow semantic intent, not software versions

v0.x allows additive changes

Breaking changes will only occur at v1.0

Compatibility Rules
Adding new signals → ✅ allowed

Adding metadata → ✅ allowed

Renaming or changing meaning of signals → ❌ not allowed within the same major version

🚫 What SSP Is Not
Not a physics model

Not a simulator SDK replacement

Not tied to any specific simulator or vendor

Not opinionated about dashboards or UI

🧠 Philosophy
SSP is a contract, not an implementation.

SSP-BRIDGE implements this contract, but the schema itself is designed
to outlive any single tool, simulator, or hardware platform.

🔮 Future Extensions (Non-breaking)
Planned additions for later versions:

Signal groups / categories

Optional nested metadata

Event-based telemetry (flags, warnings)

Hardware-oriented signal mappings

These will be introduced in a backward-compatible manner.

📌 Summary
SSP frames are simple, flat, and explicit

Capabilities describe what exists and how to use it

Schema stability is prioritized over rapid changes

Designed for long-term ecosystem growth

SSP Schema v0.2
© 2026 Rushio Industries
