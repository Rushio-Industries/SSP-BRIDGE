# SSP-BRIDGE CLI Reference

This document describes command-line options for **SSP-BRIDGE v0.3.x**.

---

## Basic usage

```bash
python app.py [options]
```

---

## Core options

### `--game <id|auto>`
Selects the simulator plugin.

- `ac` — Assetto Corsa
- `acc` — Assetto Corsa Competizione
- `ams2` — Automobilista 2 (UDP/SMS, default port 5606)
- `auto` — auto-detect (tries `acc` first, then `ac`; AMS2 requires real UDP packets)

Default: `ac`

Examples:

```bash
python app.py --game ac
python app.py --game acc
python app.py --game ams2
python app.py --game auto
```

### `--hz <number>`
Telemetry update frequency in Hertz.

Default: `60`

Examples:

```bash
python app.py --hz 30
python app.py --hz 120
```

---

## Output options

### `--out <directory>`
Output directory for logs and generated files.

Default: `logs`

```bash
python app.py --out telemetry_logs
```

### `--ndjson on|off`
Enable/disable NDJSON telemetry logging.

Default: `on`

```bash
python app.py --ndjson off
```

### `--session auto|<name>`
Controls the NDJSON session filename.

- `auto` — generates `session-YYYYMMDD-HHMMSS.ndjson`
- `<name>` — custom session name (extension optional)

Default: `auto`

```bash
python app.py --session auto
python app.py --session spa_practice
```

### `--ws on|off`
Enable/disable WebSocket streaming.

Default: `on`

```bash
python app.py --ws off
```

### `--ws-host <host>`
WebSocket bind address.

Default: `127.0.0.1`

### `--ws-port <port>`
WebSocket bind port.

Default: `8765`

---

## Capabilities

### `--capabilities auto|off|<path>`
Controls the generation of the capabilities file.

- `auto` — writes `logs/capabilities.<plugin>.json`
- `off` — disables capabilities output
- `<path>` — custom output path

Default: `auto`

```bash
python app.py --capabilities off
python app.py --capabilities caps/acc.json
```

---

## Simulator waiting behavior

### `--wait on|off`
Controls whether SSP-BRIDGE waits for the simulator to become available.

- `on` — wait and retry until detected
- `off` — fail immediately

Default: `on`

```bash
python app.py --wait off
```

### `--wait-interval <seconds>`
Seconds between retry attempts.

Default: `2.0`

```bash
python app.py --wait-interval 1.0
```

---

## Example workflows

Start bridge before launching the game:

```bash
python app.py --game auto
```

Log-only session (no WebSocket):

```bash
python app.py --ws off
```
