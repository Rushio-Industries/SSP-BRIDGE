# SSP-BRIDGE CLI Reference

This document describes all available command-line options for
**SSP-BRIDGE v0.2.x**.

---

## Basic Usage

```bash
python app.py [options]
Core Options
--game <id|auto>
Selects the simulator plugin.

ac — Assetto Corsa

auto — Automatically select the first available simulator

Default: ac

python app.py --game ac
python app.py --game auto
--hz <number>
Telemetry update frequency in Hertz.

Default: 60

python app.py --hz 30
python app.py --hz 120
Output Options
--out <directory>
Output directory for logs and generated files.

Default: logs

python app.py --out telemetry_logs
--ndjson on|off
Enable or disable NDJSON telemetry logging.

Default: on

python app.py --ndjson off
--session auto|<name>
Controls the NDJSON session filename.

auto — Generates session-YYYYMMDD-HHMMSS.ndjson

<name> — Custom session name (extension optional)

Default: auto

python app.py --session auto
python app.py --session spa_practice
--ws on|off
Enable or disable WebSocket telemetry streaming.

Default: on

python app.py --ws off
--ws-host <host>
WebSocket bind address.

Default: 127.0.0.1

--ws-port <port>
WebSocket bind port.

Default: 8765

Capabilities
--capabilities auto|off|<path>
Controls the generation of the capabilities file.

auto — Write to logs/capabilities.<plugin>.json

off — Disable capabilities output

<path> — Custom output path

Default: auto

python app.py --capabilities off
python app.py --capabilities caps/ac.json
Simulator Waiting Behavior
--wait on|off
Controls whether SSP-BRIDGE waits for the simulator to become available.

on — Wait and retry until the simulator is detected

off — Fail immediately if the simulator is not available

Default: on

python app.py --wait off
--wait-interval <seconds>
Time (in seconds) between simulator availability checks.

Default: 2.0

python app.py --wait-interval 1.0
Example Workflows
Start bridge before launching the game
python app.py --game auto
Log-only session (no WebSocket)
python app.py --ws off
Dashboard-only mode (no NDJSON)
python app.py --ndjson off
Custom output directory and session name
python app.py --out logs --session le_mans_night
Notes
All options are optional

Defaults are chosen to work out-of-the-box

CLI options are backward-compatible within the same minor version (v0.2.x)