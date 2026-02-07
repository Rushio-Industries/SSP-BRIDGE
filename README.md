# SSP-BRIDGE

**SimRacing Standard Protocol Bridge**

SSP-BRIDGE is a lightweight, extensible telemetry bridge designed to normalize sim racing data into a universal protocol, enabling plug-and-play dashboards, tools, and **hardware integrations**.

The project focuses on **runtime stability, dynamic simulator switching, and capability-driven outputs**, allowing clients and devices to adapt without game-specific logic.

---

## 🚦 Project Status

**v0.4.1 – BeamNG Plugin & Hardware-Oriented Signals**

* ✅ **Dynamic Auto-detect** (Switches games at runtime without restart)
* ✅ **Process-Aware** (Smart detection for AC/ACC on Windows)
* ✅ **Runtime Status Events** (`waiting`, `active`, `lost`)
* ✅ **Capabilities Handshake** (Full signal map on connect/switch)
* ✅ **NDJSON & WebSocket** (With sticky state support)
* ✅ **Derived Engine Signals** (`engine.rpm_max`, `engine.rpm_pct`)
* ✅ **BeamNG.drive Support** (`--game beamng` via OutGauge UDP)

---

## 🎯 Vision

Sim racing telemetry is fragmented: each simulator exposes data differently, making dashboards, tools, and hardware harder to build and maintain.

**SSP-BRIDGE aims to solve this by:**

* Providing a **standardized telemetry schema** (`ssp/0.2`)
* Acting as a **persistent state machine** between simulators and clients
* Making telemetry **easy to consume, extend, and reuse**
* Ensuring **dashboards and hardware remain connected** even when simulators restart

---

## 🧩 Architecture Overview

```text
Simulator (AC, ACC, AMS2, BeamNG)
        ↓
   SSP-BRIDGE  ←  (State Machine: Waiting / Active / Lost)
        ↓
 Universal SSP Frame (NDJSON / WebSocket / Serial)
        ↓
Dashboards · Tools · Hardware · Analytics
````

**Key principles:**

* **State-Driven:** Explicit lifecycle events prevent state spam.
* **Process-Aware:** Prioritizes running processes to avoid false positives.
* **Capability-First:** Clients adapt based on the handshake, not assumptions.

---

## 📦 Supported Simulators

### Assetto Corsa (AC)

* **Detection:** Process priority + Shared Memory.

### Assetto Corsa Competizione (ACC)

* **Detection:** Process priority + Shared Memory (+ static data for RPM limits).

### Automobilista 2 (AMS2)

* **Detection:** UDP telemetry (SMS / Project CARS protocol).

### BeamNG.drive (BeamNG)

* **Detection:** Process-aware (Windows) + UDP OutGauge telemetry.

---

## 📤 Outputs

### NDJSON (Log File / Stdout)

* **Format:** One JSON object per frame.
* **Use case:** Logging, replay, post-session analysis.

### WebSocket (Real-Time)

* **Behavior:** Sticky state (clients receive last known state on connect).
* **Use case:** Live dashboards and overlay tools.

### Serial (USB / COM Port)

* **Format:** NDJSON (one frame per line).
* **Use case:** Arduino, ESP32, shift lights, displays.
* **Design:** Rate-limited and non-blocking to protect microcontrollers.

---

## 📐 SSP Frame Example (v0.4.1)

### Capabilities Handshake

```json
{
  "type": "capabilities",
  "ts": 1769902700.90,
  "source": "acc",
  "schema": "ssp/0.2",
  "capabilities": {
    "plugin": "acc",
    "schema": "ssp/0.2",
    "signals": {
      "engine.rpm": { "type": "integer", "unit": "rpm" },
      "engine.rpm_max": { "type": "integer", "unit": "rpm" },
      "engine.rpm_pct": { "type": "number", "unit": "%", "min": 0, "max": 100 },
      "vehicle.speed_kmh": { "type": "number", "unit": "km/h" },
      "drivetrain.gear": { "type": "integer" }
    }
  }
}
```

### Telemetry Frame

```json
{
  "v": "0.2",
  "ts": 1769902700.94,
  "source": "acc",
  "signals": {
    "engine.rpm": 7200,
    "engine.rpm_max": 8000,
    "engine.rpm_pct": 90.0,
    "vehicle.speed_kmh": 145.5,
    "drivetrain.gear": 4,
    "controls.throttle_pct": 100.0,
    "controls.brake_pct": 0.0
  }
}
```

> Signals are **optional**. If a signal is unavailable, it is omitted.

---

## 🔌 Hardware & Microcontrollers

SSP-BRIDGE is designed to be **hardware-friendly by default**.

* Stable signal names
* NDJSON (one line per frame)
* Capability-based discovery
* No simulator-specific logic required

Microcontrollers may parse only the signals they need (for example, `engine.rpm_pct` for a shift light).

---

## ⚡ Quick Start (Windows)

### Requirements

* Python **3.12+**
* A supported simulator

### Run

```bash
py app.py --game auto
```

```bash
py app.py --game beamng
```

---

## 🔄 Runtime Model

> **waiting → active → lost → waiting**

---

## 🗺️ Roadmap (High Level)

* ✅ v0.2: Plugin loader and CLI
* ✅ v0.3: Multi-simulator support (AC / ACC / AMS2)
* ✅ v0.4: Hardware-friendly signals + BeamNG
* v0.5+: More simulators and richer telemetry
* v1.0: Stable SSP specification and SDKs

---

## 📄 License

MIT License

© Rushio Industries

Maintained by Muzonho — Founder of Rushio Industries
