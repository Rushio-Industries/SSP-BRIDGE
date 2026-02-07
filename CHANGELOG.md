# Changelog

## v0.4.1

### Added
- BeamNG.drive plugin (`--game beamng`) using official OutGauge UDP telemetry.
- BeamNG integrated into dynamic runtime auto-detect (conservative probing).

### Improved
- Hardware-oriented derived signals remain consistent across supported sims:
  - `engine.rpm_max`
  - `engine.rpm_pct`

### Notes
- No breaking changes to telemetry schema (`ssp/0.2`).
- Clients should treat missing signals as “not available” (not zero).

## v0.4.0

### Added

* Serial output (NDJSON over USB/COM) for microcontrollers (Arduino, ESP32, etc).
* Normalized RPM signals:

  * `engine.rpm_max`
  * `engine.rpm_pct`
* ACC support for dynamic RPM limits via static shared memory (`carModel` + `maxRpm`).
* AMS2 support for RPM limits via UDP telemetry when available.
* Hardware-oriented output design (rate-limited, non-blocking).

### Improved

* Capability-driven signaling for RPM-related data (signals are emitted only when valid).
* Clear rules for optional signals (omitted when unavailable).
* Documentation updated to reflect hardware-focused workflows.
* Output architecture aligned for software and hardware consumers.

### Notes

* No breaking changes to the SSP schema (`ssp/0.2`).
* Fully compatible with v0.3.x dashboards and clients.
* AC plugin behavior unchanged and remains stable.
* `engine.rpm_pct` is only emitted when a reliable `engine.rpm_max` is known.

---

## v0.3.3

### Added

* Official SSP protocol specification (`PROTOCOL.md`).
* Frozen Core Signals set for `ssp/0.2`.
* Extended capabilities metadata (min/max/precision where applicable).
* Minimal protocol shape tests to prevent regressions.

### Improved

* Documentation alignment between README and implementation.
* Clear separation between protocol, bridge, and client responsibilities.

### Notes

* No breaking changes to telemetry schema (`ssp/0.2`).
* Fully compatible with v0.3.2 dashboards and clients.

---

## v0.3.2

### Added

* Dynamic `--game auto` runtime: switch simulators without restarting the bridge.
* Runtime status events:

  * `waiting`
  * `active`
  * `lost`
* Capabilities handshake emitted on simulator connect or switch.
* WebSocket sticky state (status + capabilities for late-connecting clients).
* Process-aware simulator prioritization on Windows to avoid AC/ACC confusion.

### Improved

* Smarter auto-detect: plugins must produce real telemetry frames to activate.
* Runtime stability during simulator restarts and loading phases.
* ACC process monitoring with cached and fault-tolerant checks.

### Notes

* Telemetry schema remains `ssp/0.2` (no breaking changes).
* NDJSON and WebSocket outputs remain compatible with v0.3.x clients.

---

## v0.3.1

### Added

* Automobilista 2 plugin (`--game ams2`) via UDP (SMS / Project CARS protocol).
* AMS2 capabilities export (`capabilities.ams2.json`) following the same `ssp/0.2` format.

### Fixed

* AMS2 plugin waits for real UDP packets before declaring the sim “available”
  (avoids false positives in `--game auto`).

### Docs

* Updated README and CLI docs to include AMS2 and setup notes.