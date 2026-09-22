"""토큰/비밀번호를 원문 대신 서버 비밀키로 다이제스트하는 보안 유틸리티."""

import hashlib
import hmac

from .config import APP_SECRET


def digest(value: str) -> str:
    """문자열을 HMAC-SHA256 16진수 문자열로 변환합니다.

    단순 SHA256만 사용하면 동일한 입력은 어디서나 같은 해시가 만들어지지만,
    HMAC은 서버만 아는 `APP_SECRET`을 함께 사용하므로 원문 추측 공격에 더 강합니다.
    """
    return hmac.new(
        APP_SECRET.encode(),
        value.encode(),
        hashlib.sha256,
    ).hexdigest()
