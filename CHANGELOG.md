# Changelog

## v0.3.1

### Added
- Automobilista 2 plugin (`--game ams2`) via UDP (SMS / Project CARS protocol).
- AMS2 capabilities export (`capabilities.ams2.json`) following the same `ssp/0.2` format.

### Fixed
- AMS2 plugin waits for real UDP packets before declaring the sim “available” (avoids false positives in `--game auto` flows).

### Docs
- Updated README and CLI docs to include AMS2 and setup notes.
