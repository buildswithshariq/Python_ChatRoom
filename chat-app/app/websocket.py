import json
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import WebSocket


@dataclass
class Connection:
    websocket: WebSocket
    user_id: int
    username: str
    room_id: int


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, dict[int, Connection]] = {}

    async def connect(self, room_id: int, user_id: int, username: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self._connections:
            self._connections[room_id] = {}
        self._connections[room_id][user_id] = Connection(
            websocket=websocket, user_id=user_id, username=username, room_id=room_id
        )

        await self.broadcast(
            room_id,
            {
                "type": "system",
                "content": f"{username} joined the room",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            exclude_user_id=user_id,
        )

        await self.broadcast_user_list(room_id)

    def disconnect(self, room_id: int, user_id: int):
        if room_id in self._connections and user_id in self._connections[room_id]:
            del self._connections[room_id][user_id]
            if not self._connections[room_id]:
                del self._connections[room_id]

    async def broadcast(self, room_id: int, message: dict, exclude_user_id: int | None = None):
        if room_id not in self._connections:
            return
        dead = []
        for uid, conn in self._connections[room_id].items():
            if uid == exclude_user_id:
                continue
            try:
                await conn.websocket.send_text(json.dumps(message))
            except Exception:
                dead.append(uid)

        for uid in dead:
            self.disconnect(room_id, uid)

        if dead:
            await self.broadcast_user_list(room_id)

    async def broadcast_user_list(self, room_id: int):
        online = self.get_online_users(room_id)
        await self.broadcast(
            room_id,
            {"type": "user_list", "users": online},
        )

    def get_online_users(self, room_id: int) -> list[dict]:
        if room_id not in self._connections:
            return []
        return [
            {"user_id": c.user_id, "username": c.username}
            for c in self._connections[room_id].values()
        ]

    async def send_personal(self, user_id: int, room_id: int, message: dict):
        if room_id in self._connections and user_id in self._connections[room_id]:
            try:
                await self._connections[room_id][user_id].websocket.send_text(json.dumps(message))
            except Exception:
                self.disconnect(room_id, user_id)


manager = ConnectionManager()
