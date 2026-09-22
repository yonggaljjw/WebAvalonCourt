"""게스트 세션 생성/조회."""
import secrets
import time

from sqlalchemy import text

from ..core.database import engine
from ..core.security import digest
from ..domain.game import require

SESSION_SECONDS = 7 * 86400


def get_session(token):
    require(bool(token), "닉네임으로 먼저 입장해주세요.")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT pid,name,expires FROM sessions "
                "WHERE token=:token"
            ),
            {"token": digest(token)},
        ).mappings().first()
    require(
        row is not None and row["expires"] > time.time(),
        "입장 정보가 만료되었습니다. 다시 입장해주세요.",
    )
    return dict(row)


def create_session(name):
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
    return token, {"pid": pid, "name": name}
