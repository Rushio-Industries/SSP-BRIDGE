# Changelog

## v0.3.2

### Added
- Dynamic `--game auto` runtime: switch simulators without restarting the bridge.
- Runtime status events:
  - `waiting`
  - `active`
  - `lost`
- Capabilities handshake emitted on simulator connect or switch.
- WebSocket sticky state (status + capabilities for late-connecting clients).
- Process-aware simulator prioritization on Windows to avoid AC/ACC confusion.

### Improved
- Smarter auto-detect: plugins must produce real telemetry frames to activate.
- Runtime stability during simulator restarts and loading phases.
- ACC process monitoring with cached and fault-tolerant checks.

### Notes
- Telemetry schema remains `ssp/0.2` (no breaking changes).
- NDJSON and WebSocket outputs remain compatible with v0.3.x clients.

---

## v0.3.1

### Added
- Automobilista 2 plugin (`--game ams2`) via UDP (SMS / Project CARS protocol).
- AMS2 capabilities export (`capabilities.ams2.json`) following the same `ssp/0.2` format.

### Fixed
- AMS2 plugin waits for real UDP packets before declaring the sim “available”
  (avoids false positives in `--game auto`).

### Docs
- Updated README and CLI docs to include AMS2 and setup notes.