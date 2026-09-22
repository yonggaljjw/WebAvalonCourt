"""실시간 게임 행동과 채팅을 처리하는 WebSocket 라우터."""

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
    """한 플레이어의 WebSocket 연결을 유지하며 메시지를 계속 수신합니다."""

    # 브라우저가 허용된 웹 페이지에서 연결한 것인지 Origin을 먼저 검사합니다.
    if websocket.headers.get("origin") not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    # 쿠키 세션, 방, 참가자 존재 여부를 연결 승인 전에 검증합니다.
    try:
        user = get_session(websocket.cookies.get("avalon_session"))
        room = get_room(code)
        player = room.player(user["pid"])
        require(not player.departed, "이미 퇴장한 방입니다.")
    except RuleError:
        await websocket.close(code=1008)
        return

    # 여기까지 검증에 성공해야 WebSocket handshake를 최종 수락합니다.
    await websocket.accept()
    key = (code, player.id)

    async with lock:
        # 동일 세션이 다른 탭에서 다시 연결되면 기존 소켓을 닫고 새 연결만 유지합니다.
        old = connections.get(key)
        connections[key] = websocket
        if old:
            await old.close(code=4001)

        player.connected = True
        player.seen = time.time()

        # 재접속으로 일시정지가 풀릴 수 있으므로 즉시 tick 후 전체 상태를 전파합니다.
        room.tick(time.time())
        await broadcast(room)

    # 너무 빠른 액션 반복을 막기 위한 마지막 행동 시각입니다.
    last_action = 0

    try:
        # WebSocket은 HTTP와 달리 한 연결 안에서 여러 메시지를 계속 받습니다.
        while True:
            raw = await websocket.receive_text()
            require(len(raw) <= 4096, "메시지가 너무 큽니다.")

            try:
                data = json.loads(raw)
                require(isinstance(data, dict), "잘못된 요청입니다.")

                async with lock:
                    # 다른 탭이 같은 세션으로 연결해 현재 소켓이 교체되었는지 확인합니다.
                    require(
                        connections.get(key) is websocket,
                        "다른 창에서 접속했습니다.",
                    )

                    # 어떤 메시지든 정상 수신되면 마지막 활동 시각을 갱신합니다.
                    player.seen = time.time()

                    # ping은 게임 행동이 아니라 연결 생존 확인용 heartbeat입니다.
                    if data.get("action") == "ping":
                        player.connected = True
                        room.tick(time.time())
                        await websocket.send_json({"type": "pong"})
                        continue

                    # 0.15초보다 빠른 연속 요청은 실수/스팸성 중복 전송으로 간주합니다.
                    require(
                        time.time() - last_action >= 0.15,
                        "너무 빠른 요청입니다.",
                    )
                    last_action = time.time()

                    # 행동 직전에 현재 방의 timeout/재접속 상태를 한 번 반영합니다.
                    room.tick(time.time())

                    if data.get("action") == "chat":
                        # 채팅은 게임 규칙 action과 분리해 별도로 검증/저장합니다.
                        message = data.get("message", "")
                        require(
                            isinstance(message, str)
                            and 0 < len(message.strip()) <= 300,
                            "채팅은 1~300자로 입력해주세요.",
                        )

                        room.chat.append(
                            {
                                # 클라이언트가 보내는 sender_id를 믿지 않고 서버에서 직접 기록합니다.
                                "id": secrets.token_hex(12),
                                "sender_id": player.id,
                                "name": player.name,
                                "message": message.strip(),
                                "at": time.time(),
                            }
                        )

                        # 채팅 기록은 최근 100개만 유지해 상태 payload가 끝없이 커지지 않게 합니다.
                        room.chat = room.chat[-100:]
                    else:
                        # ready/propose/vote/quest 등의 규칙 판단은 도메인 객체가 담당합니다.
                        room.action(player.id, data.get("action"), data)

                    room.updated = time.time()
                    save_rooms(rooms)

                    # 한 사람의 행동으로 상태가 바뀌면 방의 모든 연결에 최신 상태를 보냅니다.
                    await broadcast(room)

            except (RuleError, ValueError, TypeError) as exc:
                # 잘못된 입력은 연결을 끊지 않고 해당 사용자에게 오류 메시지만 돌려줍니다.
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": (
                            str(exc)
                            if isinstance(exc, RuleError)
                            else "요청 형식을 확인해주세요."
                        ),
                    }
                )

    except (WebSocketDisconnect, RuleError):
        # 브라우저가 정상 종료되거나 연결 수준 규칙 오류가 나면 finally에서 상태를 정리합니다.
        pass
    finally:
        async with lock:
            # 이 소켓이 여전히 현재 연결일 때만 제거합니다.
            # 새 탭이 이미 connections를 교체했다면 새 연결까지 지우면 안 됩니다.
            if connections.get(key) is websocket:
                connections.pop(key, None)
                player.connected = False
                player.seen = time.time()
                room.tick(time.time())
                save_rooms(rooms)
                await broadcast(room)
