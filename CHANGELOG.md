# Changelog

## v0.3.0

### Added
- ACC plugin (`--game acc`) with standardized SSP v0.2 output.
- Standardized **capabilities format** across plugins (`ssp/0.2`).
- Included `controls.throttle_pct` and `controls.brake_pct` in ACC capabilities (no clutch).

### Fixed
- `--game auto` now prefers **ACC first** to avoid AC false-positives.
- AC frames now report `v: "0.2"` (was inconsistent).

### Docs
- Refreshed README + CLI docs.
- Added SSP schema documentation (`docs/schema.md`).
