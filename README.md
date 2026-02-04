# SSP-BRIDGE

**SimRacing Standard Protocol Bridge**

SSP-BRIDGE is a lightweight telemetry bridge that **normalizes sim racing data into a universal JSON schema** (SSP),
so dashboards/tools can be built once and work across simulators.

---

## 🚦 Project Status

**v0.3.1 – Stable core + AC/ACC/AMS2 support**

✅ Plugin-first architecture  
✅ CLI (`--game ac|acc|ams2|auto`)  
✅ NDJSON session logging  
✅ WebSocket real-time streaming  
✅ Capabilities export for feature discovery  
✅ Unified SSP frame + capabilities format across plugins   

---

## 🎯 Vision

Sim telemetry is fragmented: each simulator exposes different shapes/units.
SSP-BRIDGE provides:

- A **standardized telemetry frame**
- A simple bridge from simulator → apps/hardware
- **Capabilities** so clients adapt automatically (no hardcoding per sim)

---

## 📦 Supported Simulators

### Assetto Corsa (`ac`)
Shared Memory source (`acpmf_physics`).

### Assetto Corsa Competizione (`acc`)
WinAPI shared memory mapping (`Local\acpmf_physics`).

### Automobilista 2 (`ams2`)
UDP telemetry (SMS / Project CARS protocol).  
Default UDP port: **5606** (configure AMS2 to match).

> **Note about `--game auto`:** ACC is tried first to avoid false positives.
AC's mapping can exist even when the game isn't running.
AMS2 is only considered “available” after receiving real UDP packets.

---

## 📐 SSP Frame (schema v0.2)

Example frame:

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

Signals currently standardized across AC + ACC:

- `engine.rpm`
- `vehicle.speed_kmh`
- `drivetrain.gear`
- `controls.throttle_pct`
- `controls.brake_pct`
- *(no clutch by design for now)*

---

## 🔍 Feature Discovery (Capabilities)

A capabilities file describes which signals exist + metadata (type/unit/hz).

Default path:

- `logs/capabilities.<plugin_id>.json`

---

## 📤 Outputs

### NDJSON (log file)
- Default: `logs/session-YYYYMMDD-HHMMSS.ndjson`
- 1 JSON object per line (easy replay/analysis)

### WebSocket (live stream)
- Default: `ws://127.0.0.1:8765`
- Real-time telemetry streaming for dashboards/tools

---

## ⚡ Quick Start (Windows)

### Requirements
- Python 3.12+
- Run a supported simulator **in-session**

### Install
```bash
pip install -r requirements.txt
```

### Run
```bash
# Pick explicitly
python app.py --game ac
python app.py --game acc
python app.py --game ams2

# Or auto-detect
python app.py --game auto

---

## 📚 Documentation

- [SSP Schema](docs/schema.md)
- [CLI Reference](docs/cli.md)

---

## 🗺️ Roadmap (High Level)

- **v0.3.x:** Expand game support while keeping SSP output stable
- **v0.4:** Hardware-oriented outputs (Serial / UDP / CAN)
- **v1.0:** Stable SSP specification + SDKs

---

## 📄 License

MIT License

---

Created and maintained by Muzonho (Rushio Industries).  
© 2026 Rushio Industries
