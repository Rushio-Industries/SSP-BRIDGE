Com certeza! Mantive exatamente a **estrutura visual e a filosofia** do seu layout antigo ("SimRacing Standard Protocol Bridge"), mas atualizei todo o conteúdo técnico para refletir a **versão v0.3.2** (suporte a AMS2, ACC, sistema de *handshake*, detecção de processos no Windows, etc.).

Aqui está o resultado unificado:

---

# SSP-BRIDGE

**SimRacing Standard Protocol Bridge**

SSP-BRIDGE is a lightweight, extensible telemetry bridge designed to normalize sim racing data into a universal protocol, enabling plug-and-play dashboards, tools, and future hardware integrations.

The project focuses on **runtime stability, dynamic simulator switching, and capability-driven outputs**, allowing clients to adapt without game-specific logic.

---

## 🚦 Project Status

**v0.3.2 – Dynamic Runtime & Dashboard Foundation**

* ✅ **Dynamic Auto-detect** (Switches games at runtime without restart)
* ✅ **Process-Aware** (Smart detection for AC/ACC on Windows)
* ✅ **Runtime Status Events** (`waiting`, `active`, `lost`)
* ✅ **Capabilities Handshake** (Full signal map on connect)
* ✅ **Smarter Probing** (Active only on real telemetry data)
* ✅ **NDJSON & WebSocket** (With sticky state support)

---

## 🎯 Vision

Sim racing telemetry is fragmented: each simulator exposes data differently, making dashboards, tools, and hardware harder to build and maintain.

**SSP-BRIDGE aims to solve this by:**

* Providing a **standardized telemetry schema** (`ssp/0.2`)
* Acting as a **persistent state machine** between simulators and apps
* Making telemetry **easy to consume, extend, and reuse**
* ensuring **dashboards remain connected** even when simulators restart

---

## 🧩 Architecture Overview

```text
Simulator (AC, ACC, AMS2)
        ↓
   SSP-BRIDGE  ←  (State Machine: Waiting / Active / Lost)
        ↓
 Universal SSP Frame
        ↓
Dashboards · Tools · Hardware · Analytics

```

**Key principles:**

* **State-Driven:** Explicit lifecycle events prevent "state spam".
* **Process-Aware:** Prioritizes running processes to avoid false positives (Windows).
* **Capability-First:** Clients adapt based on the handshake, not hardcoded assumptions.

---

## 📦 Supported Simulators

### Assetto Corsa (AC)

* **Detection:** Process priority + Shared Memory.

### Assetto Corsa Competizione (ACC)

* **Detection:** Process priority + Shared Memory.

### Automobilista 2 (AMS2)

* **Detection:** Shared Memory polling.

---

## 📤 Outputs

### NDJSON (Log File / Stdout)

* **Format:** One JSON object per frame.
* **Use case:** Logging, replay, and post-session analysis.

### WebSocket (Real-Time)

* **Behavior:** Sticky state (clients receive the last known state on connect).
* **Use case:** Live dashboards and overlay tools.

---

## 📐 SSP Frame Example (v0.3.2)

**1. Capabilities Handshake (On Connect/Switch):**

```json
{
  "type": "capabilities",
  "schema": "ssp/0.2",
  "source": "acc",
  "capabilities": {
    "engine.rpm": { "type": "int", "min": 0, "max": 10000 },
    "vehicle.speed_kmh": { "type": "float" }
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
    "vehicle.speed_kmh": 145.5,
    "drivetrain.gear": 4,
    "controls.throttle_pct": 100.0,
    "controls.brake_pct": 0.0
  }
}

```

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

SSP-BRIDGE runs as a persistent state machine to ensure dashboard stability:

> **waiting** → **active** → **lost** → **waiting**

* **Waiting:** No simulator detected.
* **Active:** Telemetry is flowing smoothly.
* **Lost:** Simulator disconnected or stalled (events are deduplicated).

---

## 🛠️ Development Philosophy

* Minimal dependencies
* Explicit, readable code
* No hidden magic
* Built to scale from software → hardware

---

## 🤝 Contributing

Contributions are welcome — especially:

* New simulator plugins (iRacing, rFactor 2)
* Dashboard integrations
* Documentation improvements

---

## 📄 License

MIT License

© Rushio Industries