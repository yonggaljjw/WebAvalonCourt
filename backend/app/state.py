"""단일 worker에서 공유하는 인메모리 런타임 상태."""
import asyncio

rooms = {}
connections = {}
lock = asyncio.Lock()
