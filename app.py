import argparse
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

import websockets

from ssp_bridge.plugins.registry import create_plugin, auto_detect_plugin
from ssp_bridge.outputs.ndjson import NdjsonWriter
from ssp_bridge.outputs.ws import WSBroadcaster
from ssp_bridge.outputs.serial_out import SerialOut
from ssp_bridge.core.derived import RpmMaxTracker, add_engine_rpm_pct


# Deduplication state (avoid repeating identical status events).
_last_status_key = None  # (state, source)


def make_status_event(state: str, source: str | None) -> dict:
    return {
        "type": "status",
        "ts": time.time(),
        "state": state,    # waiting | active | lost
        "source": source,  # ac | acc | ams2 | None
    }


def make_capabilities_event(source: str, caps: dict) -> dict:
    return {
        "type": "capabilities",
        "ts": time.time(),
        "source": source,
        "schema": "ssp/0.2",
        "capabilities": caps,
    }


def parse_args():
    p = argparse.ArgumentParser(prog="ssp-bridge", description="SimRacing Standard Protocol Bridge")
    p.add_argument("--game", default="ac", help="plugin id (ac, acc, ams2, beamng, auto)")
    p.add_argument("--hz", type=float, default=60.0, help="loop frequency (default: 60)")
    p.add_argument("--out", default="logs", help="output directory (default: logs)")
    p.add_argument("--ndjson", choices=["on", "off"], default="on", help="enable NDJSON logging")
    p.add_argument("--ws", choices=["on", "off"], default="on", help="enable WebSocket streaming")
    p.add_argument("--capabilities", default="auto", help="capabilities output: auto | off | <path>")
    p.add_argument("--session", default="auto", help="ndjson session name: auto | <name>")
    p.add_argument("--wait", choices=["on", "off"], default="on", help="wait for simulator to be available")
    p.add_argument("--wait-interval", type=float, default=2.0, help="seconds between retry attempts")
    p.add_argument("--ws-host", default="127.0.0.1")
    p.add_argument("--ws-port", type=int, default=8765)
    p.add_argument("--serial-out", default=None, help="Send NDJSON lines via Serial COM:BAUD (example: COM3:115200)",)
    return p.parse_args()


def make_session_filename(args) -> str:
    if args.session.strip().lower() == "auto":
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"session-{ts}.ndjson"
    name = args.session.strip()
    if not name:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"session-{ts}"
    if not name.endswith(".ndjson"):
        name += ".ndjson"
    return name


def resolve_capabilities_path(args, out_dir: Path, plugin_id: str) -> Path | None:
    mode = args.capabilities.strip().lower()
    if mode == "off":
        return None
    if mode == "auto":
        return out_dir / f"capabilities.{plugin_id}.json"
    return Path(args.capabilities)


async def main():
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rpm_tracker = RpmMaxTracker(publish_min_rpm=3000)


    # --- Output Handlers Setup ---
    nd = None
    nd_path = None
    if args.ndjson == "on":
        nd_path = out_dir / make_session_filename(args)
        nd = NdjsonWriter(str(nd_path))

    ws = None
    server = None
    if args.ws == "on":
        ws = WSBroadcaster()
        server = await websockets.serve(ws.handler, args.ws_host, args.ws_port)

    serial_out = None
    if args.serial_out:
        parts = args.serial_out.split(":")
        port = parts[0].strip()
        baud = int(parts[1]) if len(parts) > 1 and parts[1].strip() else 115200
        serial_out = SerialOut(port, baud)

        

    # --- Communication Helpers ---
    def emit(obj: dict):
        line = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        # stdout
        print(line)
        # websocket
        if ws:
            ws.update_sticky(obj)
        # ndjson file
        if nd:
            nd.write(obj)
        # serial out
        if serial_out:
            serial_out.send_line(line)

    async def emit_async(obj: dict):
        """Async wrapper for emit that broadcasts to WebSocket."""
        emit(obj)
        if ws:
            await ws.broadcast(obj)

    async def emit_status(state: str, source: str | None):
        global _last_status_key
        key = (state, source)
        if key == _last_status_key:
            return
        _last_status_key = key
        await emit_async(make_status_event(state, source))

    async def emit_capabilities(source: str, plugin):
        await emit_async(make_capabilities_event(source, plugin.capabilities()))

    # --- Plugin Initialization ---
    game = args.game.strip().lower()
    plugin = None

    # Emit "waiting" before entering the detection loop.
    await emit_status("waiting", None)

    while plugin is None:
        try:
            if game == "auto":
                plugin = auto_detect_plugin()
            else:
                plugin = create_plugin(game)
                plugin.open()
        except Exception as e:
            if args.wait == "off":
                raise RuntimeError(f"Failed to open simulator ({args.game}): {e}") from e
            print(f"Waiting for simulator ({args.game})... ({e})")
            await asyncio.sleep(max(args.wait_interval, 0.2))

    # Emit "active" + capabilities on first detection.
    print(f"{plugin.name} detected, starting telemetry.")
    await emit_status("active", plugin.id)
    await emit_capabilities(plugin.id, plugin)

    # --- Capabilities Export (File) ---
    cap_path = resolve_capabilities_path(args, out_dir, plugin.id)
    if cap_path is not None:
        cap_path.parent.mkdir(parents=True, exist_ok=True)
        cap_path.write_text(
            json.dumps(plugin.capabilities(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    print("SSP-BRIDGE v0.4.0")
    print(f"Plugin: {plugin.id} - {plugin.name}")
    print(f"Capabilities: {cap_path if cap_path else 'off'}")
    print(f"NDJSON: {nd_path if nd else 'off'}")
    print(f"WebSocket: ws://{args.ws_host}:{args.ws_port}" if args.ws == "on" else "WebSocket: off")

    # --- Main Loop ---
    emit_period = 1.0 / max(args.hz, 1.0)
    poll_sleep = min(0.005, emit_period / 4.0)

    latest_frame: dict | None = None

    # Controls fixed-rate output.
    next_emit = time.time()

    # NEW: prevents re-emitting cached frames that did not update.
    last_seen_frame_ts = None       # ts of the latest observed frame
    last_emitted_frame_ts = None    # ts of the last emitted frame
    rpm_tracker.reset()

    try:
        while True:
            try:
                frame = plugin.read_frame()
            except Exception as e:
                if args.wait == "on":
                    print(f"Telemetry lost ({e}). Waiting for simulator...")
                    await emit_status("lost", plugin.id if plugin else None)
                    await emit_status("waiting", None)

                    try:
                        if plugin:
                            plugin.close()
                    except Exception:
                        pass
                    plugin = None

                    # Dynamic re-detection loop.
                    while True:
                        try:
                            if game == "auto":
                                plugin = auto_detect_plugin()
                            else:
                                plugin = create_plugin(game)
                                plugin.open()

                            print(f"{plugin.name} detected, resuming telemetry.")
                            await emit_status("active", plugin.id)
                            await emit_capabilities(plugin.id, plugin)
                            break
                        except Exception:
                            await asyncio.sleep(max(args.wait_interval, 0.5))

                    latest_frame = None
                    last_seen_frame_ts = None
                    last_emitted_frame_ts = None
                    next_emit = time.time()
                    continue
                else:
                    raise

            if frame is not None:
                latest_frame = frame

                # Track newest observed frame timestamp (used for dedup).
                ts = frame.get("ts")
                if ts is not None:
                    last_seen_frame_ts = ts

            # --- Emit at fixed rate (ONLY when a NEW frame exists) ---
            now = time.time()
            if latest_frame is not None and now >= next_emit:
                # Only emit if we observed a newer frame since the last emit.
                # This stops NDJSON/WS from being filled with identical frames.
                if last_seen_frame_ts is not None and last_seen_frame_ts != last_emitted_frame_ts:
                    try:
                        sig = latest_frame.get("signals", {})
                        add_engine_rpm_pct(sig, rpm_tracker)
                    except Exception:
                        pass

                    await emit_async(latest_frame)

                    last_emitted_frame_ts = last_seen_frame_ts

                next_emit = now + emit_period

            await asyncio.sleep(poll_sleep)

    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if server:
            server.close()
            await server.wait_closed()
        if nd:
            nd.close()
        try:
            if plugin:
                plugin.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())