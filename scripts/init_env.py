"""`.env.example`을 복사하면서 필요한 비밀값을 안전한 난수로 채우는 초기화 스크립트."""

from pathlib import Path
import secrets

# 이 스크립트의 상위 프로젝트 루트에 .env를 생성합니다.
path = Path(__file__).resolve().parents[1] / ".env"

# 기존 .env를 덮어쓰면 운영 비밀번호/세션 키가 바뀔 수 있으므로 즉시 중단합니다.
if path.exists():
    raise SystemExit(".env가 이미 있습니다. 기존 비밀값을 보존합니다.")

# 예제 파일을 템플릿처럼 읽어옵니다.
sample = (path.parent / ".env.example").read_text(encoding="utf-8")

# APP_SECRET, MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD의 세 GENERATE_ME를 차례대로 교체합니다.
# token_urlsafe()는 쉘/Docker Compose에서 다루기 쉬운 URL-safe 문자열을 생성합니다.
for _ in range(3):
    sample = sample.replace("GENERATE_ME", secrets.token_urlsafe(36), 1)

path.write_text(sample, encoding="utf-8")

# Unix 계열에서는 소유자만 읽고 쓸 수 있도록 권한을 좁힙니다.
# Windows에서는 chmod 의미가 다를 수 있으므로 실패해도 실행을 계속합니다.
try:
    path.chmod(0o600)
except OSError:
    pass

print(".env 생성 완료. docker compose up --build -d 로 실행하세요.")
