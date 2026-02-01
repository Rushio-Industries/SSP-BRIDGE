import asyncio
import time
import json
from pathlib import Path

from ssp_bridge.plugins.ac.shared_memory import ACPhysicsView
from ssp_bridge.core.frame import to_ssp_frame_ac
from ssp_bridge.core.capabilities import CAPABILITIES_AC_V01
from ssp_bridge.outputs.ndjson import NdjsonWriter
from ssp_bridge.outputs.ws import WSBroadcaster
import websockets

async def main():
    Path("logs").mkdir(exist_ok=True)

    # salva capabilities (bom pra devs e dashboards)
    Path("logs/capabilities.ac.json").write_text(json.dumps(CAPABILITIES_AC_V01, indent=2), encoding="utf-8")

    phys = ACPhysicsView()
    nd = NdjsonWriter("logs/session.ndjson")
    ws = WSBroadcaster()

    server = await websockets.serve(ws.handler, "127.0.0.1", 8765)

    try:
        while True:
            frame = to_ssp_frame_ac(phys.data)
            nd.write(frame)
            await ws.broadcast(frame)
            await asyncio.sleep(1/60)  # 60 Hz
    finally:
        server.close()
        await server.wait_closed()
        nd.close()
        phys.close()

if __name__ == "__main__":
    asyncio.run(main())
