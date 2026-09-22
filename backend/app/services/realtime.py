"""WebSocket 상태 전파와 1초 주기의 서버 시계 처리."""

import asyncio
import time

from ..core.database import save_rooms
from ..state import connections, lock, rooms


async def broadcast(room):
    """현재 방의 최신 상태를 연결된 모든 참가자에게 전송합니다."""
    for player in room.players:
        websocket = connections.get((room.code, player.id))
        if not websocket:
            continue

        try:
            # player마다 room.view(player.id)를 따로 만들어 비밀 정보 노출을 방지합니다.
            # 2초 안에 전송이 끝나지 않으면 느리거나 끊긴 연결로 판단합니다.
            await asyncio.wait_for(
                websocket.send_json(
                    {"type": "state", "room": room.view(player.id)}
                ),
                2,
            )
        except Exception:
            # 이 함수에서 전체 게임을 중단시키지 않고 연결 상태만 false로 바꿉니다.
            # 이후 clock_loop()의 재접속 규칙이 실제 중단 여부를 결정합니다.
            player.connected = False


async def clock_loop():
    """서버가 살아있는 동안 매초 방의 시간/연결 상태를 점검합니다."""
    while True:
        await asyncio.sleep(1)

        # 여러 WebSocket/HTTP 요청과 동시에 rooms를 수정하지 않도록 공용 Lock을 사용합니다.
        async with lock:
            changed = False

            # 순회 도중 방을 삭제할 수 있으므로 list() 복사본을 사용합니다.
            for room in list(rooms.values()):
                now = time.time()
                before = (room.phase, room.pause_since)

                # 15초 동안 ping이나 메시지가 전혀 없으면 연결이 끊긴 것으로 표시합니다.
                for player in room.players:
                    if player.connected and now - player.seen > 15:
                        player.connected = False

                # 대기실에서는 일정 시간 돌아오지 않는 사용자의 좌석을 자동 정리합니다.
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

                        # 아무도 남지 않은 대기실은 방 자체를 삭제합니다.
                        if not retained:
                            del rooms[room.code]
                            continue

                        # 방장이 사라졌다면 남은 첫 플레이어에게 방장을 넘깁니다.
                        if room.host not in {player.id for player in retained}:
                            room.host = retained[0].id

                        await broadcast(room)

                # 진행 중 방의 재접속 일시정지/시간초과 판정은 도메인 객체에게 맡깁니다.
                room.tick(now)
                if before != (room.phase, room.pause_since):
                    changed = True
                    await broadcast(room)

                # 24시간 동안 활동이 없고 아무도 연결되지 않은 대기/종료 방은 정리합니다.
                if (
                    now - room.updated > 86400
                    and room.phase in ("lobby", "ended")
                    and not any(player.connected for player in room.players)
                ):
                    del rooms[room.code]
                    changed = True

            # 실제 상태가 달라진 주기에만 DB 스냅샷을 갱신합니다.
            if changed:
                save_rooms(rooms)
