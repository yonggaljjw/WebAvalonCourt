"""FastAPI 프로세스의 시작과 종료 시점에 실행할 작업."""

import asyncio
from contextlib import asynccontextmanager, suppress

from .core.database import close_engine, initialize_storage, save_rooms
from .services.realtime import clock_loop
from .state import rooms


@asynccontextmanager
async def lifespan(app):
    """서버 시작 전 초기화 → 실행 → 종료 정리를 한 함수로 표현합니다."""
    # 1. DB 테이블을 준비하고 저장된 방 스냅샷을 메모리로 복원합니다.
    initialize_storage(rooms)
    # 재시작으로 무효 종료된 상태 등이 있다면 즉시 DB에도 다시 반영합니다.
    save_rooms(rooms)

    # 2. 1초마다 연결/제한시간을 확인하는 비동기 백그라운드 태스크를 실행합니다.
    task = asyncio.create_task(clock_loop())

    # yield 이전은 startup, yield 이후는 shutdown 시점에 실행됩니다.
    yield

    # 3. 서버 종료 시 시계 태스크를 취소하고 정상적으로 정리될 때까지 기다립니다.
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task

    # 4. 마지막으로 SQLAlchemy 커넥션 풀을 닫습니다.
    close_engine()
