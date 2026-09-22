"""REST API 라우터: 세션과 방 관리."""
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

router = APIRouter(prefix="/api")


def current(request):
    return get_session(request.cookies.get("avalon_session"))


@router.get("/health")
def health():
    healthcheck()
    return {"status": "ok"}


@router.get("/me")
def me(request: Request):
    return current(request)


@router.post("/guest")
async def guest(body: Guest, response: Response, request: Request):
    name = body.name.strip()
    require(name, "닉네임을 입력해주세요.")

    old = None
    try:
        old = current(request)
    except RuleError:
        pass
    if old:
        require(
            not player_is_in_any_room(old["pid"]),
            "방에서 먼저 나가주세요.",
        )

    token, user = create_session(name)
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
    user = current(request)
    async with lock:
        require(len(rooms) < 200, "방 개수 한도에 도달했습니다.")
        require(
            not player_is_in_any_room(user["pid"]),
            "기존 방에서 먼저 나가주세요.",
        )
        code = secrets.token_hex(3).upper()
        while code in rooms:
            code = secrets.token_hex(3).upper()
        room = Room(
            code,
            body.title.strip() or "원탁의 기사들",
            user["pid"],
            validate_settings(body.settings),
            digest(body.password) if body.password else "",
        )
        room.players.append(Player(user["pid"], user["name"]))
        rooms[code] = room
        save_rooms(rooms)
        return {"code": code}


@router.post("/rooms/{code}/join")
async def join_room(code: str, body: JoinRoom, request: Request):
    user = current(request)
    async with lock:
        room = get_room(code)
        if any(
            player.id == user["pid"] and not player.departed
            for player in room.players
        ):
            return {"code": code}
        require(room.phase == "lobby", "진행 중이거나 종료된 방입니다.")
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
        await broadcast(room)
    return {"code": code}


@router.put("/rooms/{code}/settings")
async def update_settings(code: str, body: Settings, request: Request):
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
        for player in room.players:
            player.ready = False
        save_rooms(rooms)
        await broadcast(room)
    return {"ok": True}


@router.post("/rooms/{code}/leave")
async def leave_room(code: str, request: Request):
    user = current(request)
    async with lock:
        room = get_room(code)
        require(
            not room.player(user["pid"]).departed,
            "이미 퇴장한 방입니다.",
        )
        if room.phase not in ("lobby", "ended"):
            room.finish(
                "aborted",
                f'{user["name"]} 님이 퇴장하여 게임을 무효 종료했습니다.',
            )
        await broadcast(room)

        websocket = connections.pop((code, user["pid"]), None)
        if websocket:
            await websocket.close()

        if room.phase == "lobby":
            room.players = [
                player for player in room.players if player.id != user["pid"]
            ]
            room.leader = 0
        else:
            player = room.player(user["pid"])
            player.departed = True
            player.connected = False

        if not any(not player.departed for player in room.players):
            del rooms[code]
        elif room.host == user["pid"]:
            room.host = next(
                player.id for player in room.players if not player.departed
            )

        save_rooms(rooms)
        if code in rooms:
            await broadcast(room)
    return {"ok": True}
