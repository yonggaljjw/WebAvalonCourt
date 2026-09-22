"""SQLAlchemy 엔진과 최소 DB 접근 기능."""
import json
import time
from dataclasses import asdict

from sqlalchemy import create_engine, text

from .config import DATABASE_URL
from ..domain.game import Player, Room

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def initialize_storage(rooms):
    """테이블을 준비하고 저장된 방 상태를 메모리로 복원합니다."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS room_state "
                "(code VARCHAR(12) PRIMARY KEY, payload LONGTEXT NOT NULL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS sessions "
                "(token VARCHAR(64) PRIMARY KEY, pid VARCHAR(32) NOT NULL, "
                "name VARCHAR(48) NOT NULL, expires DOUBLE NOT NULL)"
            )
        )
        connection.execute(
            text("DELETE FROM sessions WHERE expires < :now"),
            {"now": time.time()},
        )
        for row in connection.execute(text("SELECT payload FROM room_state")):
            data = json.loads(row[0])
            data["players"] = [Player(**player) for player in data["players"]]
            room = Room(**data)
            for player in room.players:
                player.connected = False
            if room.phase not in ("lobby", "ended"):
                room.finish(
                    "aborted",
                    "서버가 재시작되어 게임을 무효 종료했습니다.",
                )
            rooms[room.code] = room


def save_rooms(rooms):
    """현재 메모리 방 상태를 한 트랜잭션으로 저장합니다."""
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM room_state"))
        for room in rooms.values():
            connection.execute(
                text(
                    "INSERT INTO room_state (code, payload) "
                    "VALUES (:code, :payload)"
                ),
                {
                    "code": room.code,
                    "payload": json.dumps(asdict(room), ensure_ascii=False),
                },
            )


def healthcheck():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def close_engine():
    engine.dispose()
