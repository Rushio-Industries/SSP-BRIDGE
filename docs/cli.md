# SSP-BRIDGE CLI Reference

This document describes command-line options for **SSP-BRIDGE v0.4.x**.

---

## Basic usage

```bash
python app.py [options]
````

---

## Core options

### `--game <id|auto>`

Selects the simulator plugin.

* `ac` — Assetto Corsa
* `acc` — Assetto Corsa Competizione
* `ams2` — Automobilista 2 (UDP / SMS protocol)
* `beamng` — BeamNG.drive (OutGauge UDP, default port 4444)
* `auto` — auto-detect (ACC → AC → AMS2 when valid telemetry is detected)

Default: `ac`

Examples:

```bash
python app.py --game ac
python app.py --game acc
python app.py --game ams2
python app.py --game auto
```

---

### `--hz <number>`

Telemetry update frequency in Hertz.

This value controls how often telemetry frames are generated internally.
Some outputs (for example, Serial) may apply additional rate limits.

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

---

### `--ndjson on|off`

Enable or disable NDJSON telemetry logging.

Default: `on`

```bash
python app.py --ndjson off
```

---

### `--session auto|<name>`

Controls the NDJSON session filename.

* `auto` — generates `session-YYYYMMDD-HHMMSS.ndjson`
* `<name>` — custom session name (extension optional)

Default: `auto`

```bash
python app.py --session auto
python app.py --session spa_practice
```

---

### `--ws on|off`

Enable or disable WebSocket streaming.

Default: `on`

```bash
python app.py --ws off
```

---

### `--ws-host <host>`

WebSocket bind address.

Default: `127.0.0.1`

---

### `--ws-port <port>`

WebSocket bind port.

Default: `8765`

---

## Serial Output (Hardware)

### `--serial <port>`

Enable serial output (NDJSON over USB/COM).

This output is designed for microcontrollers such as Arduino and ESP32.

Examples:

* Windows: `COM3`
* Linux: `/dev/ttyUSB0`
* macOS: `/dev/tty.usbserial-XXXX`

```bash
python app.py --serial COM3
```

---

### `--serial-baud <baudrate>`

Serial baud rate.

Default: `115200`

```bash
python app.py --serial COM3 --serial-baud 115200
```

---

### `--serial-rate <hz>`

Maximum number of lines per second sent over serial.

This protects slower devices from being flooded with data.

Default: `60`

```bash
python app.py --serial COM3 --serial-rate 30
```

---

## Capabilities

### `--capabilities auto|off|<path>`

Controls the generation of the capabilities file.

* `auto` — writes `logs/capabilities.<plugin>.json`
* `off` — disables capabilities output
* `<path>` — custom output path

Default: `auto`

```bash
python app.py --capabilities off
python app.py --capabilities caps/acc.json
```

---

## Simulator waiting behavior

### `--wait on|off`

Controls whether SSP-BRIDGE waits for the simulator to become available.

* `on` — wait and retry until detected
* `off` — fail immediately

Default: `on`

```bash
python app.py --wait off
```

---

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

Hardware-focused workflow (Arduino):

```bash
python app.py --game auto --serial COM3 --serial-rate 30
```
