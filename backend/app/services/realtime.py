"""WebSocket 전파와 서버 시계 처리."""
import asyncio
import time

from ..core.database import save_rooms
from ..state import connections, lock, rooms


async def broadcast(room):
    for player in room.players:
        websocket = connections.get((room.code, player.id))
        if websocket:
            try:
                await asyncio.wait_for(
                    websocket.send_json(
                        {"type": "state", "room": room.view(player.id)}
                    ),
                    2,
                )
            except Exception:
                player.connected = False


async def clock_loop():
    while True:
        await asyncio.sleep(1)
        async with lock:
            changed = False
            for room in list(rooms.values()):
                now = time.time()
                before = (room.phase, room.pause_since)

                for player in room.players:
                    if player.connected and now - player.seen > 15:
                        player.connected = False

                if room.phase == "lobby":
                    retained = [
                        player
                        for player in room.players
                        if player.connected
                        or now - player.seen
                        < max(15, room.settings["reconnect_seconds"])
                    ]
                    if len(retained) != len(room.players):
                        room.players = retained
                        room.leader = 0
                        changed = True
                        if not retained:
                            del rooms[room.code]
                            continue
                        if room.host not in {player.id for player in retained}:
                            room.host = retained[0].id
                        await broadcast(room)

                room.tick(now)
                if before != (room.phase, room.pause_since):
                    changed = True
                    await broadcast(room)

                if (
                    now - room.updated > 86400
                    and room.phase in ("lobby", "ended")
                    and not any(player.connected for player in room.players)
                ):
                    del rooms[room.code]
                    changed = True

            if changed:
                save_rooms(rooms)
