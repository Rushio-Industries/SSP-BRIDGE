# SSP-BRIDGE

**SimRacing Standard Protocol Bridge**

SSP-BRIDGE is a lightweight, extensible telemetry bridge designed to normalize sim racing data into a universal protocol, enabling plug-and-play dashboards, tools, and future hardware integrations.

This project focuses on **clarity, openness, and community-driven extensibility**, inspired by platforms like Arduino — but for sim racing telemetry.

---

## 🚦 Project Status

**v0.1.0 – Stable (Assetto Corsa)**

- ✅ Assetto Corsa Shared Memory support  
- ✅ Universal SSP Frame v0.1  
- ✅ NDJSON logging  
- ✅ WebSocket real-time telemetry streaming  
- ✅ Feature discovery via capabilities file  

More simulators and features are planned.

---

## 🎯 Vision

Sim racing telemetry is fragmented: each simulator exposes data differently, making dashboards, tools, and hardware harder to build and maintain.

**SSP-BRIDGE aims to solve this by:**
- Providing a **standardized telemetry schema**
- Acting as a **bridge** between simulators and applications
- Making telemetry **easy to consume, extend, and reuse**
- Enabling future **plug-and-play hardware dashboards**

---

## 🧩 Architecture Overview

```

Simulator (AC, AMS2, ACC, ...)
↓
SSP-BRIDGE
↓
Universal SSP Frame
↓
Dashboards · Tools · Hardware · Analytics

````

Key principles:
- Modular plugins per simulator
- Clear separation between input, core, and outputs
- No dependency on proprietary tools (e.g. SimHub)

---

## 📦 Supported Simulator

### Assetto Corsa
- Data source: Shared Memory
- Signals available in v0.1:
  - Engine RPM
  - Vehicle speed (km/h)
  - Gear
  - Throttle (%)
  - Brake (%)

---

## 📤 Outputs

### NDJSON (Log File)
- Path: `logs/session.ndjson`
- One JSON object per frame
- Ideal for logging, replay, and analysis

### WebSocket (Live Stream)
- URL: `ws://127.0.0.1:8765`
- Real-time telemetry streaming
- Ideal for dashboards and live tools

---

## 📐 SSP Frame Example

```json
{
  "v": "0.1",
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

## 🔍 Feature Discovery (Capabilities)

SSP-BRIDGE exposes a capabilities file describing all available signals:

* Path: `logs/capabilities.ac.json`
* Purpose:

  * Allows dashboards/tools to adapt automatically
  * Avoids hardcoded assumptions per simulator

---

## ⚡ Quick Start (Windows)

### Requirements

* Python **3.12+**
* Assetto Corsa (running and in-session)

### Steps

```bash
pip install -r requirements.txt
python app.py
```

Then:

* Start driving in Assetto Corsa
* Telemetry will be available via WebSocket and NDJSON

---

## 🛠️ Development Philosophy

* Minimal dependencies
* Explicit, readable code
* No hidden magic
* Built to scale from software → hardware

---

## 🗺️ Roadmap (High Level)

* v0.2: Plugin loader and CLI (`--game ac`, `--game auto`)
* v0.3: Additional simulators (AMS2 / ACC)
* v0.4: Hardware-oriented outputs (serial / CAN / UDP)
* v1.0: Stable SSP specification and SDKs

---

## 🤝 Contributing

Contributions are welcome — especially:

* New simulator plugins
* Additional telemetry signals
* Dashboard integrations
* Documentation improvements

Open an issue before large changes.

---

## 📄 License

MIT License
© Rushio Industries
