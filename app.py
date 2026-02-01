import argparse
import asyncio
import json
from pathlib import Path

import websockets

from ssp_bridge.plugins.registry import create_plugin, auto_detect_plugin
from ssp_bridge.outputs.ndjson import NdjsonWriter
from ssp_bridge.outputs.ws import WSBroadcaster


def parse_args():
    p = argparse.ArgumentParser(prog="ssp-bridge")
    p.add_argument("--game", default="ac", help="plugin id (e.g. ac, auto)")
    p.add_argument("--hz", type=float, default=60.0, help="loop frequency (default: 60)")

    # outputs
    p.add_argument("--out", default="logs", help="output directory (default: logs)")
    p.add_argument("--ndjson", choices=["on", "off"], default="on", help="enable NDJSON logging")
    p.add_argument("--ws", choices=["on", "off"], default="on", help="enable WebSocket streaming")

    # websocket config
    p.add_argument("--ws-host", default="127.0.0.1")
    p.add_argument("--ws-port", type=int, default=8765)
    return p.parse_args()


async def main():
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Plugin Initialization ---
    if args.game.strip().lower() == "auto":
        plugin = auto_detect_plugin()
    else:
        plugin = create_plugin(args.game)
    
    plugin.open()

    # --- Capabilities Export ---
    cap_path = out_dir / f"capabilities.{plugin.id}.json"
    cap_path.write_text(
        json.dumps(plugin.capabilities(), indent=2, ensure_ascii=False), 
        encoding="utf-8"
    )

    # --- Output Handlers Setup ---
    nd = None
    if args.ndjson == "on":
        nd = NdjsonWriter(out_dir / "session.ndjson")

    # --- WebSocket Server Setup ---
    ws = None
    server = None
    if args.ws == "on":
        ws = WSBroadcaster()
        server = await websockets.serve(ws.handler, args.ws_host, args.ws_port)

    # --- Prints de Status ---
    print(f"SSP-BRIDGE v0.2.1")
    print(f"Plugin: {plugin.id} - {plugin.name}")
    print(f"Capabilities: {cap_path}")
    print(f"NDJSON: {out_dir / 'session.ndjson' if args.ndjson == 'on' else 'off'}")
    print(f"WebSocket: ws://{args.ws_host}:{args.ws_port}" if args.ws == "on" else "WebSocket: off")

    # --- Main Loop ---
    period = 1.0 / max(args.hz, 1.0)
    try:
        while True:
            frame = plugin.read_frame()

            if frame:
                if nd is not None:
                    nd.write(frame)

                if ws is not None:
                    await ws.broadcast(frame)

            await asyncio.sleep(period)
            
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        # --- Cleanup ---
        if server is not None:
            server.close()
            await server.wait_closed()

        if nd is not None:
            nd.close()

        plugin.close()
        print("\nBridge closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass