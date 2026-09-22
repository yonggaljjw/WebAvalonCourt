"""실시간 게임 행동 WebSocket 라우터."""
import json
import secrets
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.config import ALLOWED_ORIGINS
from ..core.database import save_rooms
from ..domain.game import RuleError, require
from ..services.realtime import broadcast
from ..services.room_service import get_room
from ..services.session_service import get_session
from ..state import connections, lock, rooms

router = APIRouter()


@router.websocket("/ws/{code}")
async def websocket_endpoint(websocket: WebSocket, code: str):
    if websocket.headers.get("origin") not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    try:
        user = get_session(websocket.cookies.get("avalon_session"))
        room = get_room(code)
        player = room.player(user["pid"])
        require(not player.departed, "이미 퇴장한 방입니다.")
    except RuleError:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    key = (code, player.id)
    async with lock:
        old = connections.get(key)
        connections[key] = websocket
        if old:
            await old.close(code=4001)
        player.connected = True
        player.seen = time.time()
        room.tick(time.time())
        await broadcast(room)

    last_action = 0
    try:
        while True:
            raw = await websocket.receive_text()
            require(len(raw) <= 4096, "메시지가 너무 큽니다.")
            try:
                data = json.loads(raw)
                require(isinstance(data, dict), "잘못된 요청입니다.")
                async with lock:
                    require(
                        connections.get(key) is websocket,
                        "다른 창에서 접속했습니다.",
                    )
                    player.seen = time.time()
                    if data.get("action") == "ping":
                        player.connected = True
                        room.tick(time.time())
                        await websocket.send_json({"type": "pong"})
                        continue

                    require(
                        time.time() - last_action >= 0.15,
                        "너무 빠른 요청입니다.",
                    )
                    last_action = time.time()
                    room.tick(time.time())

                    if data.get("action") == "chat":
                        message = data.get("message", "")
                        require(
                            isinstance(message, str)
                            and 0 < len(message.strip()) <= 300,
                            "채팅은 1~300자로 입력해주세요.",
                        )
                        room.chat.append(
                            {
                                "id": secrets.token_hex(12),
                                "sender_id": player.id,
                                "name": player.name,
                                "message": message.strip(),
                                "at": time.time(),
                            }
                        )
                        room.chat = room.chat[-100:]
                    else:
                        room.action(player.id, data.get("action"), data)

                    room.updated = time.time()
                    save_rooms(rooms)
                    await broadcast(room)
            except (RuleError, ValueError, TypeError) as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(exc)
                        if isinstance(exc, RuleError)
                        else "요청 형식을 확인해주세요.",
                    }
                )
    except (WebSocketDisconnect, RuleError):
        pass
    finally:
        async with lock:
            if connections.get(key) is websocket:
                connections.pop(key, None)
                player.connected = False
                player.seen = time.time()
                room.tick(time.time())
                save_rooms(rooms)
                await broadcast(room)
