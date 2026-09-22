# `routers` — 외부 요청의 입구

FastAPI의 `APIRouter`를 이용해 URL별 처리 함수를 분리한 폴더입니다.

## HTTP와 WebSocket을 나눈 이유

- `http.py`: 방 목록 조회, 게스트 세션 생성, 방 생성/입장/퇴장, 설정 저장처럼 **한 번 요청하고 응답받는 작업**
- `websocket.py`: 준비, 팀 제안, 투표, 원정 카드, 채팅처럼 **게임 중 계속 실시간으로 오가는 작업**

라우터는 가능한 한 게임 규칙을 직접 구현하지 않습니다. 실제 규칙은 `domain/game.py`, 재사용 로직은 `services/`로 넘깁니다.

## 학습 포인트

- `@router.get/post/put(...)`: HTTP 엔드포인트 등록
- `@router.websocket(...)`: WebSocket 엔드포인트 등록
- `async with lock`: 여러 비동기 요청이 동시에 같은 방 상태를 수정하지 못하게 보호
- `await broadcast(room)`: 상태 변경 후 연결된 참가자에게 최신 상태 전달
