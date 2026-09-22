# Backend 학습 가이드

이 폴더는 **FastAPI + SQLAlchemy + MySQL + WebSocket**으로 구성된 서버입니다.
프론트엔드가 보내는 HTTP/WebSocket 요청을 받아 게임 규칙을 실행하고, 방 상태를 저장하고, 참가자에게 실시간 상태를 다시 전달합니다.

## 먼저 알아둘 개념

- **FastAPI**: Python으로 REST API와 WebSocket 서버를 만드는 웹 프레임워크입니다.
- **ASGI**: 비동기 통신을 지원하는 Python 웹 서버 규격입니다. 이 프로젝트의 `main.py`에 있는 `app` 객체가 ASGI 진입점입니다.
- **REST API**: 방 생성, 입장, 설정 변경처럼 요청-응답으로 끝나는 작업에 사용합니다.
- **WebSocket**: 채팅, 준비, 투표, 원정처럼 서버와 브라우저가 연결을 유지하며 실시간으로 주고받는 작업에 사용합니다.
- **SQLAlchemy**: Python 코드에서 DB 연결과 SQL 실행을 다루는 라이브러리입니다. 이 프로젝트는 ORM 모델 대신 `text()` SQL을 직접 사용합니다.

## 요청 처리 흐름

```text
브라우저
  ├─ HTTP /api/... ──────> app/routers/http.py
  └─ WebSocket /ws/... ─> app/routers/websocket.py
                              ↓
                        app/services/
                              ↓
                        app/domain/game.py
                              ↓
                     app/core/database.py
                              ↓
                            MySQL
```

`routers`는 요청을 받고, `services`는 공통 업무를 처리하고, `domain`은 게임 규칙을 담당합니다. 이 경계를 지키면 기능이 커져도 한 파일에 모든 코드가 몰리지 않습니다.

## 추천 읽기 순서

1. `app/main.py` — 서버가 어디서 시작되는지
2. `app/factory.py` — FastAPI 앱과 라우터가 어떻게 조립되는지
3. `app/routers/http.py` — 일반 API 흐름
4. `app/routers/websocket.py` — 실시간 통신 흐름
5. `app/domain/game.py` — 실제 아발론 규칙
6. `app/services/` — 여러 라우터가 공유하는 로직
7. `app/core/` — DB/설정/보안 같은 기반 기능
8. `tests/` — 규칙이 코드로 어떻게 검증되는지
