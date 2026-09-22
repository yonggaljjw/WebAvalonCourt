"""REST API 라우터: 익명 세션과 방의 생성/조회/입장/설정/퇴장을 처리합니다."""

import hmac
import secrets
import time

from fastapi import APIRouter, Request, Response

from ..core.config import COOKIE_SECURE
from ..core.database import healthcheck, save_rooms
from ..core.security import digest
from ..domain.game import Player, Room, RuleError, require
from ..schemas import CreateRoom, Guest, JoinRoom, Settings
from ..services.realtime import broadcast
from ..services.room_service import (
    get_room,
    player_is_in_any_room,
    validate_settings,
)
from ..services.session_service import SESSION_SECONDS, create_session, get_session
from ..state import connections, lock, rooms

# 이 파일의 모든 HTTP API 앞에는 /api가 붙습니다.
router = APIRouter(prefix="/api")


def current(request):
    """요청 쿠키에서 현재 익명 사용자 정보를 꺼내는 공통 도우미입니다."""
    return get_session(request.cookies.get("avalon_session"))


@router.get("/health")
def health():
    """컨테이너/프록시가 백엔드와 DB 상태를 확인할 때 사용하는 헬스체크입니다."""
    healthcheck()
    return {"status": "ok"}


@router.get("/me")
def me(request: Request):
    """현재 브라우저의 익명 세션 정보를 반환합니다."""
    return current(request)


@router.post("/guest")
async def guest(body: Guest, response: Response, request: Request):
    """닉네임을 받아 새 익명 세션을 만들고 HttpOnly 쿠키로 토큰을 저장합니다."""
    name = body.name.strip()
    require(name, "닉네임을 입력해주세요.")

    # 이미 유효한 세션이 있다면 사용자가 현재 어느 방에도 없어야 닉네임을 바꿀 수 있습니다.
    old = None
    try:
        old = current(request)
    except RuleError:
        # 세션이 없거나 만료된 경우는 새 세션을 만들면 되므로 무시합니다.
        pass

    if old:
        require(
            not player_is_in_any_room(old["pid"]),
            "방에서 먼저 나가주세요.",
        )

    token, user = create_session(name)

    # HttpOnly=True이므로 브라우저 JavaScript에서 토큰 값을 직접 읽을 수 없습니다.
    response.set_cookie(
        "avalon_session",
        token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=SESSION_SECONDS,
    )
    return user


@router.get("/rooms")
async def list_rooms():
    """로비에 보여줄 공개 가능한 방 정보만 요약해서 반환합니다."""
    return [
        {
            "code": room.code,
            "title": room.title,
            "count": len(room.players),
            "capacity": room.settings["capacity"],
            "phase": room.phase,
            "locked": bool(room.password_hash),
            "roles": room.settings["roles"],
        }
        for room in rooms.values()
    ]


@router.post("/rooms")
async def create_room(body: CreateRoom, request: Request):
    """새 게임방을 만들고 요청한 사용자를 첫 참가자/방장으로 등록합니다."""
    user = current(request)

    # 방 생성은 공유 상태를 수정하므로 다른 요청과 겹치지 않도록 Lock을 잡습니다.
    async with lock:
        require(len(rooms) < 200, "방 개수 한도에 도달했습니다.")
        require(
            not player_is_in_any_room(user["pid"]),
            "기존 방에서 먼저 나가주세요.",
        )

        # 3바이트 난수를 6자리 대문자 16진수 문자열로 바꿔 초대 코드를 만듭니다.
        code = secrets.token_hex(3).upper()
        while code in rooms:
            code = secrets.token_hex(3).upper()

        room = Room(
            code,
            body.title.strip() or "원탁의 기사들",
            user["pid"],
            validate_settings(body.settings),
            # 비밀번호 원문은 저장하지 않고 HMAC 다이제스트만 저장합니다.
            digest(body.password) if body.password else "",
        )
        room.players.append(Player(user["pid"], user["name"]))
        rooms[code] = room

        # 메모리 상태 변경 후 DB 스냅샷을 맞춥니다.
        save_rooms(rooms)
        return {"code": code}


@router.post("/rooms/{code}/join")
async def join_room(code: str, body: JoinRoom, request: Request):
    """기존 대기실 방에 현재 사용자를 참가시킵니다."""
    user = current(request)

    async with lock:
        room = get_room(code)

        # 같은 사용자가 새로고침/재요청한 경우 중복 참가자를 만들지 않습니다.
        if any(
            player.id == user["pid"] and not player.departed
            for player in room.players
        ):
            return {"code": code}

        require(room.phase == "lobby", "진행 중이거나 종료된 방입니다.")

        # compare_digest()는 문자열 비교 시간 차이를 줄이는 보안용 비교 함수입니다.
        require(
            not room.password_hash
            or hmac.compare_digest(room.password_hash, digest(body.password)),
            "방 비밀번호가 틀립니다.",
        )
        require(
            len(room.players) < room.settings["capacity"],
            "방이 가득 찼습니다.",
        )
        require(
            not player_is_in_any_room(user["pid"]),
            "기존 방에서 먼저 나가주세요.",
        )
        require(
            not any(player.name == user["name"] for player in room.players),
            "이 방에 같은 닉네임이 있습니다.",
        )

        room.players.append(Player(user["pid"], user["name"]))
        room.updated = time.time()
        save_rooms(rooms)

        # 이미 연결된 다른 참가자에게 인원 변화가 즉시 보이도록 상태를 전파합니다.
        await broadcast(room)

    return {"code": code}


@router.put("/rooms/{code}/settings")
async def update_settings(code: str, body: Settings, request: Request):
    """방장이 대기실의 게임 설정을 변경합니다."""
    user = current(request)

    async with lock:
        room = get_room(code)
        require(
            room.host == user["pid"] and room.phase == "lobby",
            "방장만 대기실에서 설정할 수 있습니다.",
        )
        require(
            body.capacity >= len(room.players),
            "현재 인원보다 작은 정원은 설정할 수 없습니다.",
        )

        room.settings = validate_settings(body)

        # 설정이 바뀌었는데 기존 준비 상태를 유지하면 의도치 않게 바로 시작할 수 있으므로 초기화합니다.
        for player in room.players:
            player.ready = False

        save_rooms(rooms)
        await broadcast(room)

    return {"ok": True}


@router.post("/rooms/{code}/leave")
async def leave_room(code: str, request: Request):
    """현재 사용자를 방에서 내보내고 필요하면 방장 이양/게임 무효 종료를 처리합니다."""
    user = current(request)

    async with lock:
        room = get_room(code)
        require(
            not room.player(user["pid"]).departed,
            "이미 퇴장한 방입니다.",
        )

        # 진행 중 게임에서의 명시적 퇴장은 단순 재접속이 아니므로 무효 종료합니다.
        if room.phase not in ("lobby", "ended"):
            room.finish(
                "aborted",
                f'{user["name"]} 님이 퇴장하여 게임을 무효 종료했습니다.',
            )

        # 종료 상태를 먼저 전송해 남은 참가자가 왜 끝났는지 볼 수 있게 합니다.
        await broadcast(room)

        # 퇴장 사용자의 WebSocket 연결이 남아 있다면 끊습니다.
        websocket = connections.pop((code, user["pid"]), None)
        if websocket:
            await websocket.close()

        if room.phase == "lobby":
            # 대기실에서는 좌석 자체를 제거합니다.
            room.players = [
                player for player in room.players if player.id != user["pid"]
            ]
            room.leader = 0
        else:
            # 종료된 게임에서는 결과 화면의 역할 공개를 위해 플레이어 기록은 남깁니다.
            player = room.player(user["pid"])
            player.departed = True
            player.connected = False

        # 남은 사람이 하나도 없으면 방을 삭제합니다.
        if not any(not player.departed for player in room.players):
            del rooms[code]
        # 방장이 나갔으면 남은 첫 참가자에게 방장 권한을 넘깁니다.
        elif room.host == user["pid"]:
            room.host = next(
                player.id for player in room.players if not player.departed
            )

        save_rooms(rooms)

        # 방이 아직 존재한다면 최종 인원/방장 상태를 다시 알려줍니다.
        if code in rooms:
            await broadcast(room)

    return {"ok": True}
