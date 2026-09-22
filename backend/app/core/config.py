"""환경변수 기반 애플리케이션 설정.

Docker Compose가 주입한 환경변수를 이 모듈에서 한 번 읽어 두고,
나머지 코드에서는 `os.environ`을 직접 뒤지지 않고 설정 상수를 import해서 사용합니다.
"""

import os
from urllib.parse import quote_plus

# 세션 토큰과 방 비밀번호 다이제스트에 사용할 서버 비밀키입니다.
# 필수값이므로 없으면 애플리케이션 시작 단계에서 바로 오류가 납니다.
APP_SECRET = os.environ["APP_SECRET"]

# 브라우저의 HTTP 쓰기 요청과 WebSocket 연결을 허용할 Origin 목록입니다.
# 쉼표로 구분된 문자열을 set으로 바꿔 membership 검사를 빠르고 단순하게 합니다.
ALLOWED_ORIGINS = set(
    os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
)

# HTTPS 운영에서는 Secure 쿠키를 사용해야 하므로 환경변수로 켜고 끕니다.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false") == "true"

# DATABASE_URL을 직접 지정할 수도 있고, 없으면 MySQL 관련 환경변수로 URL을 조립합니다.
# 사용자명/비밀번호에 특수문자가 있을 수 있어 quote_plus()로 URL 인코딩합니다.
DATABASE_URL = os.getenv("DATABASE_URL") or (
    "mysql+pymysql://"
    + quote_plus(os.environ["MYSQL_USER"])
    + ":"
    + quote_plus(os.environ["MYSQL_PASSWORD"])
    + "@db/"
    + quote_plus(os.environ["MYSQL_DATABASE"])
    + "?charset=utf8mb4"
)
