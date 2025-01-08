from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends

class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, uuid: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[uuid] = websocket

    def disconnect(self, uuid: str):
        if uuid in self.active_connections:
            del self.active_connections[uuid]

    async def send_personal_message(self, uuid: str, message: dict):
        websocket = self.active_connections.get(uuid)
        if websocket:
            await websocket.send_json(message)