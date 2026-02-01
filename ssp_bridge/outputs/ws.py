import asyncio
import json
import websockets

class WSBroadcaster:
    def __init__(self):
        self.clients = set()

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)

    async def broadcast(self, frame: dict):
        if not self.clients:
            return
        msg = json.dumps(frame, ensure_ascii=False)
        await asyncio.gather(*(ws.send(msg) for ws in list(self.clients)), return_exceptions=True)
