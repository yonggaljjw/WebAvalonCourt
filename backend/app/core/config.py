"""환경변수 기반 애플리케이션 설정."""
import os
from urllib.parse import quote_plus

APP_SECRET = os.environ["APP_SECRET"]
ALLOWED_ORIGINS = set(
    os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false") == "true"

DATABASE_URL = os.getenv("DATABASE_URL") or (
    "mysql+pymysql://"
    + quote_plus(os.environ["MYSQL_USER"])
    + ":"
    + quote_plus(os.environ["MYSQL_PASSWORD"])
    + "@db/"
    + quote_plus(os.environ["MYSQL_DATABASE"])
    + "?charset=utf8mb4"
)
