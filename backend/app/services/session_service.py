"""회원가입 없이 사용하는 익명 게스트 세션의 생성/조회 서비스."""

import secrets
import time

from sqlalchemy import text

from ..core.database import engine
from ..core.security import digest
from ..domain.game import require

# 로그인 세션은 7일 동안 유지합니다.
SESSION_SECONDS = 7 * 86400


def get_session(token):
    """브라우저 쿠키의 원본 토큰을 받아 DB의 익명 사용자 정보를 찾습니다."""
    require(bool(token), "닉네임으로 먼저 입장해주세요.")

    # DB에는 원본 토큰이 아니라 digest(token)만 저장되어 있습니다.
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT pid,name,expires FROM sessions "
                "WHERE token=:token"
            ),
            {"token": digest(token)},
        ).mappings().first()

    # 세션이 없거나 만료되었다면 다시 닉네임 입력부터 시작하게 합니다.
    require(
        row is not None and row["expires"] > time.time(),
        "입장 정보가 만료되었습니다. 다시 입장해주세요.",
    )
    return dict(row)


def create_session(name):
    """새 익명 플레이어 ID와 세션 토큰을 생성해 DB에 저장합니다."""
    # token은 브라우저 쿠키에 저장하고, pid는 게임 내부 플레이어 식별자로 사용합니다.
    token = secrets.token_urlsafe(32)
    pid = secrets.token_hex(12)

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO sessions (token,pid,name,expires) "
                "VALUES (:token,:pid,:name,:expires)"
            ),
            {
                "token": digest(token),
                "pid": pid,
                "name": name,
                "expires": time.time() + SESSION_SECONDS,
            },
        )

    # 원본 token은 이 시점에만 클라이언트 쿠키 설정용으로 반환합니다.
    return token, {"pid": pid, "name": name}
