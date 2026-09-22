# `core` — 서버 기반 기능

게임 규칙과 직접 관련되지 않은 **환경설정, DB, 보안**을 모아둔 폴더입니다.

## `config.py`

운영체제의 환경변수를 읽어 Python 상수로 바꿉니다. 비밀번호나 DB 접속정보를 소스코드에 직접 적지 않고 `.env` → Docker Compose → 환경변수 → `config.py` 순서로 전달합니다.

## `database.py`

SQLAlchemy의 `engine`으로 MySQL에 연결합니다. 이 프로젝트는 방 하나를 여러 관계형 테이블로 쪼개지 않고 `Room` 전체를 JSON으로 직렬화하여 `room_state`에 저장합니다.

학습 포인트:
- `engine.begin()`은 트랜잭션을 시작하고 블록이 정상 종료되면 커밋합니다.
- `engine.connect()`는 단순 조회처럼 직접 커밋이 필요 없는 작업에 적합합니다.
- `pool_pre_ping=True`는 커넥션 풀에서 꺼낸 연결이 살아있는지 사용 전에 확인합니다.

## `security.py`

세션 토큰이나 방 비밀번호 원문을 DB에 그대로 저장하지 않도록 HMAC 기반 다이제스트를 만듭니다. 서버의 `APP_SECRET`이 키 역할을 합니다.
