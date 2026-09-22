"""방 조회와 설정 검증처럼 여러 라우터가 공유하는 방 관련 서비스."""

from ..domain.game import EVIL, EVIL_COUNT, require
from ..state import rooms

# 방장이 옵션으로 선택할 수 있는 특수 역할입니다.
# 멀린/암살자는 항상 포함되므로 여기에는 넣지 않습니다.
SPECIAL_ROLES = {"percival", "morgana", "mordred", "oberon"}


def get_room(code):
    """방 코드로 메모리의 Room 객체를 찾습니다."""
    require(code in rooms, "방을 찾을 수 없습니다.")
    return rooms[code]


def validate_settings(settings):
    """방 설정의 특수 역할 조합이 현재 정원에서 가능한지 검증합니다."""
    # 역할이 중복되지 않고, 서버가 허용한 특수 역할만 포함되어야 합니다.
    require(
        len(settings.roles) == len(set(settings.roles))
        and set(settings.roles) <= SPECIAL_ROLES,
        "특수 역할 설정이 올바르지 않습니다.",
    )

    # 암살자는 항상 들어가므로 악 진영 특수 역할 수 계산에 +1 합니다.
    require(
        1 + sum(role in EVIL for role in settings.roles)
        <= EVIL_COUNT[settings.capacity],
        "정원보다 악의 특수 역할이 많습니다.",
    )

    # Pydantic 모델을 Room.settings에 저장하기 쉬운 일반 dict로 변환합니다.
    return settings.model_dump()


def player_is_in_any_room(pid):
    """한 익명 사용자가 동시에 여러 방에 참가하는 것을 막기 위한 검사입니다."""
    return any(
        any(
            player.id == pid and not player.departed
            for player in room.players
        )
        for room in rooms.values()
    )
