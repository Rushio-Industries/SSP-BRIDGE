# SSP-BRIDGE

**SSP-BRIDGE** is a lightweight telemetry bridge designed to normalize and forward simulator data to dashboards, external devices, and long-running monitoring tools.

The project focuses on runtime stability, dynamic simulator switching, and capability-driven outputs, allowing clients to adapt without game-specific logic.

---

## v0.3.2 – Dynamic Runtime & Dashboard Foundation

SSP-BRIDGE v0.3.2 introduces a dynamic runtime layer designed for long-running telemetry sessions and future dashboards.

The bridge is now state-driven, process-aware (on Windows), and capable of switching simulators at runtime without restarts.

---

## Key Features

* **Dynamic Auto-detect**
Automatically switches between supported simulators at runtime (`--game auto`). No restart is required when closing one simulator and opening another.
* **Runtime Status Events**
The bridge emits explicit lifecycle events via NDJSON and WebSocket to avoid state spam:
* `waiting` – No simulator detected.
* `active` – Telemetry flowing.
* `lost` – Simulator disconnected or stalled.


* **Capabilities Handshake**
On simulator connect or switch, SSP-BRIDGE emits a full capabilities map, allowing dashboards to adapt dynamically:
```json
{
  "type": "capabilities",
  "schema": "ssp/0.2",
  "source": "acc",
  "capabilities": { ... }
}

```


* **Smarter Probing**
A simulator plugin only becomes active after producing real telemetry frames. This avoids false positives caused by idle shared memory, open UDP ports, or inactive menus.
* **AC / ACC Process Awareness (Windows)**
When running in auto mode on Windows, SSP-BRIDGE prioritizes Assetto Corsa (AC) and Assetto Corsa Competizione (ACC) based on running processes. Checks are cached and fault-tolerant to prevent mis-detection and expensive per-frame system calls.

---

## Supported Simulators

* Assetto Corsa (AC)
* Assetto Corsa Competizione (ACC)
* Automobilista 2 (AMS2)

---

## Usage

### Auto-detect (Recommended)

This mode automatically switches between AC, ACC, and AMS2 based on activity.

```bash
py app.py --game auto

```

### Force Specific Simulator

You can force the bridge to listen to a specific simulator:

```bash
py app.py --game ac
py app.py --game acc
py app.py --game ams2

```

---

## Runtime Model

SSP-BRIDGE runs as a persistent state machine:

> **waiting** → **active** → **lost** → **waiting**

Dashboards and clients remain connected even when simulators restart or switch games.

### Telemetry Output

* **Schema:** `ssp/0.2` (Stable across simulators; unsupported signals are omitted).
* **Formats:**
* **NDJSON:** File / Stdout logging.
* **WebSocket:** Real-time, sticky state for dashboards.



---

## License

MIT
