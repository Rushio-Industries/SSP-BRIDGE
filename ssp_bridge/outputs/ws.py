"""WebSocket broadcaster output.

Maintains an optional sticky event cache to replay the latest state to newly connected clients."""
import asyncio
import json
import websockets

class WSBroadcaster:
    def __init__(self):
        self.clients = set()
        # Cache the latest important events for newly connected clients.
        self._sticky = {}  # key: type -> event dict

    def update_sticky(self, event: dict):
        t = event.get("type")
        if t in ("status", "capabilities"):
            self._sticky[t] = event

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            # Send cached (sticky) events immediately after connect.
            for t in ("status", "capabilities"):
                ev = self._sticky.get(t)
                if ev is not None:
                    await websocket.send(json.dumps(ev, ensure_ascii=False))

            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)

    async def broadcast(self, event: dict):
        if not self.clients:
            return
        msg = json.dumps(event, ensure_ascii=False)

        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(msg)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.clients.discard(ws)