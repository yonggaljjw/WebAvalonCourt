"""SQLAlchemy 엔진과 최소 DB 접근 기능.

이 프로젝트는 복잡한 ORM 엔티티 대신 방 전체 상태를 JSON으로 직렬화해 저장합니다.
실시간 플레이 중에는 메모리의 `rooms`가 주 상태이고, DB는 서버 재시작 대비 스냅샷 역할을 합니다.
"""

import json
import time
from dataclasses import asdict

from sqlalchemy import create_engine, text

from .config import DATABASE_URL
from ..domain.game import Player, Room

# pool_pre_ping=True: 커넥션 풀에서 꺼낸 DB 연결이 죽어 있지 않은지 사용 전에 확인합니다.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def initialize_storage(rooms):
    """필요한 테이블을 만들고 DB에 남아 있던 방 상태를 메모리로 복원합니다."""
    # engine.begin()은 블록 전체를 하나의 트랜잭션으로 처리합니다.
    with engine.begin() as connection:
        # Room 객체 전체를 JSON 문자열(payload)로 저장하는 단순 스냅샷 테이블입니다.
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS room_state "
                "(code VARCHAR(12) PRIMARY KEY, payload LONGTEXT NOT NULL)"
            )
        )

        # 익명 로그인 세션은 토큰 다이제스트, 플레이어 ID, 닉네임, 만료시각을 저장합니다.
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS sessions "
                "(token VARCHAR(64) PRIMARY KEY, pid VARCHAR(32) NOT NULL, "
                "name VARCHAR(48) NOT NULL, expires DOUBLE NOT NULL)"
            )
        )

        # 서버 시작 시 이미 만료된 세션은 정리합니다.
        connection.execute(
            text("DELETE FROM sessions WHERE expires < :now"),
            {"now": time.time()},
        )

        # 저장된 JSON을 다시 Player/Room dataclass로 복원합니다.
        for row in connection.execute(text("SELECT payload FROM room_state")):
            data = json.loads(row[0])
            data["players"] = [Player(**player) for player in data["players"]]
            room = Room(**data)

            # 프로세스가 재시작되면 기존 WebSocket 연결은 모두 사라지므로 false로 초기화합니다.
            for player in room.players:
                player.connected = False

            # 진행 중 게임을 정확히 이어갈 수 없으므로 재시작된 게임은 무효 종료 처리합니다.
            if room.phase not in ("lobby", "ended"):
                room.finish(
                    "aborted",
                    "서버가 재시작되어 게임을 무효 종료했습니다.",
                )

            rooms[room.code] = room


def save_rooms(rooms):
    """현재 메모리의 전체 방 상태를 한 트랜잭션으로 DB에 저장합니다."""
    with engine.begin() as connection:
        # 구현을 단순하게 유지하기 위해 전체 스냅샷을 지우고 다시 넣습니다.
        # 소규모 자체 호스팅에는 단순하지만, 대규모 서비스라면 방 단위 upsert가 더 적합합니다.
        connection.execute(text("DELETE FROM room_state"))

        for room in rooms.values():
            connection.execute(
                text(
                    "INSERT INTO room_state (code, payload) "
                    "VALUES (:code, :payload)"
                ),
                {
                    "code": room.code,
                    # dataclass -> dict -> JSON 문자열 순서로 변환합니다.
                    "payload": json.dumps(asdict(room), ensure_ascii=False),
                },
            )


def healthcheck():
    """DB 연결이 정상인지 가장 가벼운 쿼리로 확인합니다."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def close_engine():
    """애플리케이션 종료 시 SQLAlchemy 커넥션 풀을 정리합니다."""
    engine.dispose()
