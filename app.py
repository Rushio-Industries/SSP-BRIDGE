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


def parse_args():
    p = argparse.ArgumentParser(prog="ssp-bridge", description="SimRacing Standard Protocol Bridge")
    p.add_argument("--game", default="ac", help="plugin id (ac, acc, ams2, auto)")
    p.add_argument("--hz", type=float, default=60.0, help="loop frequency (default: 60)")

    # outputs
    p.add_argument("--out", default="logs", help="output directory (default: logs)")
    p.add_argument("--ndjson", choices=["on", "off"], default="on", help="enable NDJSON logging")
    p.add_argument("--ws", choices=["on", "off"], default="on", help="enable WebSocket streaming")

    # capabilities
    p.add_argument("--capabilities", default="auto",
                   help="capabilities output: auto | off | <path>")

    # session naming for ndjson
    p.add_argument("--session", default="auto",
                   help="ndjson session name: auto | <name>")

    # waiting behavior
    p.add_argument("--wait", choices=["on", "off"], default="on", help="wait for simulator to be available")
    p.add_argument("--wait-interval", type=float, default=2.0, help="seconds between retry attempts")

    # websocket config
    p.add_argument("--ws-host", default="127.0.0.1")
    p.add_argument("--ws-port", type=int, default=8765)
    return p.parse_args()


# --- Helpers ---

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

    # --- Plugin Initialization (with optional waiting) ---
    game = args.game.strip().lower()
    plugin = None

    while plugin is None:
        try:
            if game == "auto":
                plugin = auto_detect_plugin()  # Já vem aberto pelo registry
            else:
                plugin = create_plugin(game)
                plugin.open()
        except Exception as e:
            if args.wait == "off":
                raise RuntimeError(f"Failed to open simulator ({args.game}): {e}") from e
            print(f"Waiting for simulator ({args.game})... ({e})")
            await asyncio.sleep(max(args.wait_interval, 0.2))

    print(f"{plugin.name} detected, starting telemetry.")

    # --- Capabilities Export ---
    cap_path = resolve_capabilities_path(args, out_dir, plugin.id)
    if cap_path is not None:
        cap_path.parent.mkdir(parents=True, exist_ok=True)
        cap_path.write_text(
            json.dumps(plugin.capabilities(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # --- Output Handlers Setup ---
    nd = None
    nd_path = None
    if args.ndjson == "on":
        nd_path = out_dir / make_session_filename(args)
        nd = NdjsonWriter(str(nd_path))

    # --- WebSocket Server Setup ---
    ws = None
    server = None
    if args.ws == "on":
        ws = WSBroadcaster()
        server = await websockets.serve(ws.handler, args.ws_host, args.ws_port)

    # --- Status Feedback ---
    print("SSP-BRIDGE v0.3.0")
    print(f"Plugin: {plugin.id} - {plugin.name}")
    print(f"Capabilities: {cap_path if cap_path else 'off'}")
    print(f"NDJSON: {nd_path if nd else 'off'}")
    print(f"WebSocket: ws://{args.ws_host}:{args.ws_port}" if args.ws == "on" else "WebSocket: off")

    # --- Main Loop ---
    # Best practice for UDP-based sims (AMS2): read as fast as needed (to avoid backlog latency),
    # but emit at a fixed rate (e.g., 60 Hz) to WS/NDJSON.
    emit_period = 1.0 / max(args.hz, 1.0)

    # Input polling: independent from emit hz. Keeps latency low without burning CPU.
    poll_sleep = min(0.005, emit_period / 4.0)  # ~200 Hz max, or quarter of emit rate

    latest_frame = None
    next_emit = time.time()

    try:
        while True:
            # --- Read (non-blocking where possible) ---
            try:
                frame = plugin.read_frame()
            except Exception as e:
                if args.wait == "on":
                    print(f"Telemetry lost ({e}). Waiting for simulator...")
                    try:
                        plugin.close()
                    except Exception:
                        pass
                    plugin = None

                    while plugin is None:
                        try:
                            if game == "auto":
                                plugin = auto_detect_plugin()
                            else:
                                plugin = create_plugin(game)
                                plugin.open()
                        except Exception:
                            await asyncio.sleep(max(args.wait_interval, 0.2))

                    print(f"{plugin.name} detected, resuming telemetry.")
                    latest_frame = None
                    next_emit = time.time()
                    continue
                else:
                    raise

            if frame is not None:
                latest_frame = frame

            # --- Emit at fixed rate (default 60 Hz) ---
            now = time.time()
            if latest_frame is not None and now >= next_emit:
                if nd:
                    nd.write(latest_frame)
                if ws:
                    await ws.broadcast(latest_frame)

                # avoid "catch-up storms" if the loop was blocked
                next_emit = now + emit_period

            await asyncio.sleep(poll_sleep)

    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        # --- Cleanup ---
        if server:
            server.close()
            await server.wait_closed()

        if nd:
            nd.close()

        if plugin:
            plugin.close()

        print("\nBridge closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
