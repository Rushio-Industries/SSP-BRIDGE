# SSP-BRIDGE

**SimRacing Standard Protocol Bridge**

SSP-BRIDGE is a lightweight, extensible telemetry bridge designed to normalize sim racing data into a universal protocol, enabling plug-and-play dashboards, tools, and **hardware integrations**.

The project focuses on **runtime stability, dynamic simulator switching, and capability-driven outputs**, allowing clients and devices to adapt without game-specific logic.

---

## 🚦 Project Status

**v0.4.0 – Hardware-Ready Telemetry & Unified Outputs**

* ✅ **Dynamic Auto-detect** (Switches games at runtime without restart)
* ✅ **Process-Aware** (Smart detection for AC/ACC on Windows)
* ✅ **Runtime Status Events** (`waiting`, `active`, `lost`)
* ✅ **Capabilities Handshake** (Full signal map on connect/switch)
* ✅ **Smarter Probing** (Active only on real telemetry data)
* ✅ **NDJSON & WebSocket Outputs**
* ✅ **Serial Output (NDJSON over USB)** for microcontrollers
* ✅ **Normalized RPM Signals** (`engine.rpm_max`, `engine.rpm_pct`)

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
Simulator (AC, ACC, AMS2)
        ↓
   SSP-BRIDGE  ←  (State Machine: Waiting / Active / Lost)
        ↓
 Universal SSP Frame (NDJSON / WebSocket / Serial)
        ↓
Dashboards · Tools · Hardware · Analytics
```

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

## 📐 SSP Frame Example (v0.4.0)

**1. Capabilities Handshake (On Connect/Switch):**

```json
{
  "type": "capabilities",
  "schema": "ssp/0.2",
  "source": "acc",
  "capabilities": {
    "engine.rpm": { "type": "int", "min": 0 },
    "engine.rpm_max": { "type": "int", "min": 0 },
    "engine.rpm_pct": { "type": "float", "min": 0.0, "max": 1.0 },
    "vehicle.speed_kmh": { "type": "float" },
    "drivetrain.gear": { "type": "int" }
  }
}
```

**2. Telemetry Frame (Active):**

```json
{
  "v": "0.2",
  "ts": 1769902700.94,
  "source": "acc",
  "signals": {
    "engine.rpm": 7200,
    "engine.rpm_max": 8000,
    "engine.rpm_pct": 0.9,
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
* A supported simulator (AC, ACC, or AMS2)

### Steps

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Run the bridge (Auto-detect Recommended):**

```bash
# Automatically switches between AC, ACC, and AMS2
py app.py --game auto
```

3. **Force a specific simulator:**

```bash
py app.py --game ac
py app.py --game acc
py app.py --game ams2
```

---

## 🔄 Runtime Model

SSP-BRIDGE runs as a persistent state machine to ensure client stability:

> **waiting** → **active** → **lost** → **waiting**

* **Waiting:** No simulator detected.
* **Active:** Telemetry flowing.
* **Lost:** Simulator disconnected or stalled (events are deduplicated).

---

## 🛠️ Development Philosophy

* Minimal dependencies
* Explicit, readable code
* No hidden magic
* Built to scale from software → hardware

---

## 🗺️ Roadmap (High Level)

* ✅ v0.2: Plugin loader and CLI (`--game ac`, `--game auto`)
* ✅ v0.3: Additional simulators (AMS2 / ACC)
* v0.4: Hardware-oriented outputs (serial ✅ / UDP ⏳)
* v1.0: Stable SSP specification and SDKs

---

## 🤝 Contributing

Contributions are welcome — especially:

* New simulator plugins (iRacing, rFactor 2)
* Dashboard integrations
* Hardware examples (Arduino, ESP32)
* Documentation improvements

---

## 📄 License

MIT License

© Rushio Industries

