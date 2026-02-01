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
    p.add_argument("--game", default="ac", help="plugin id (e.g. ac)")
    p.add_argument("--hz", type=float, default=60.0, help="loop frequency (default: 60)")
    p.add_argument("--ws-host", default="127.0.0.1")
    p.add_argument("--ws-port", type=int, default=8765)
    return p.parse_args()


async def main():
    args = parse_args()
    Path("logs").mkdir(exist_ok=True)

    # --- Plugin Initialization ---
    if args.game.strip().lower() == "auto":
        plugin = auto_detect_plugin()
    else:
        plugin = create_plugin(args.game)
    
    plugin.open()

    # --- Capabilities Export ---
    cap_path = Path(f"logs/capabilities.{plugin.id}.json")
    cap_path.write_text(
        json.dumps(plugin.capabilities(), indent=2, ensure_ascii=False), 
        encoding="utf-8"
    )

    # --- Output Handlers ---
    nd = NdjsonWriter("logs/session.ndjson")
    ws = WSBroadcaster()

    # --- WebSocket Server & Main Loop ---
    async with websockets.serve(ws.handler, args.ws_host, args.ws_port) as server:
        print(f"SSP-BRIDGE v0.2 (plugin-first)")
        print(f"Plugin: {plugin.id} - {plugin.name}")
        print(f"WebSocket: ws://{args.ws_host}:{args.ws_port}")
        print(f"NDJSON: logs/session.ndjson")
        print(f"Capabilities: {cap_path}")

        period = 1.0 / max(args.hz, 1.0)

        try:
            while True:
                frame = plugin.read_frame()
                if frame:
                    nd.write(frame)
                    await ws.broadcast(frame)
                await asyncio.sleep(period)
        except asyncio.CancelledError:
            pass
        finally:
            # --- Cleanup ---
            nd.close()
            plugin.close()
            print("\nBridge closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass