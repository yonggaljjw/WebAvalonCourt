"""세션 토큰/방 비밀번호 해시 기능."""
import hashlib
import hmac

from .config import APP_SECRET


def digest(value: str) -> str:
    return hmac.new(
        APP_SECRET.encode(), value.encode(), hashlib.sha256
    ).hexdigest()
