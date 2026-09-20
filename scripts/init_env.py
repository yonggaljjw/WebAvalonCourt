"""비밀값은 URL-safe 난수로 생성해 Compose의 $ 해석 문제를 피합니다."""
from pathlib import Path
import secrets
path=Path(__file__).resolve().parents[1]/'.env'
if path.exists():
    raise SystemExit('.env가 이미 있습니다. 기존 비밀값을 보존합니다.')
sample=(path.parent/'.env.example').read_text(encoding='utf-8')
for _ in range(3): sample=sample.replace('GENERATE_ME',secrets.token_urlsafe(36),1)
path.write_text(sample,encoding='utf-8')
try:path.chmod(0o600)
except OSError:pass
print('.env 생성 완료. docker compose up --build -d 로 실행하세요.')
