"""FastAPI 시작/종료 수명주기."""
import asyncio
from contextlib import asynccontextmanager, suppress

from .core.database import close_engine, initialize_storage, save_rooms
from .services.realtime import clock_loop
from .state import rooms


@asynccontextmanager
async def lifespan(app):
    initialize_storage(rooms)
    save_rooms(rooms)
    task = asyncio.create_task(clock_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    close_engine()
