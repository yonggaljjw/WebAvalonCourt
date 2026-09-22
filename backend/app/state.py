"""단일 Uvicorn worker 안에서 공유하는 실시간 런타임 상태.

이 상태는 프로세스 메모리에만 있으므로 여러 worker/서버로 확장하려면
Redis 같은 외부 공유 저장소/메시지 브로커가 필요합니다.
"""

import asyncio

# {방 코드: Room 객체}
rooms = {}

# {(방 코드, 플레이어 ID): WebSocket 객체}
connections = {}

# 여러 async 요청이 rooms/connections를 동시에 변경하지 않도록 보호하는 공용 Lock입니다.
lock = asyncio.Lock()
