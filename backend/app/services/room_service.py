"""방 조회와 설정 검증 등 공통 방 로직."""
from ..domain.game import EVIL, EVIL_COUNT, require
from ..state import rooms

SPECIAL_ROLES = {"percival", "morgana", "mordred", "oberon"}


def get_room(code):
    require(code in rooms, "방을 찾을 수 없습니다.")
    return rooms[code]


def validate_settings(settings):
    require(
        len(settings.roles) == len(set(settings.roles))
        and set(settings.roles) <= SPECIAL_ROLES,
        "특수 역할 설정이 올바르지 않습니다.",
    )
    require(
        1 + sum(role in EVIL for role in settings.roles)
        <= EVIL_COUNT[settings.capacity],
        "정원보다 악의 특수 역할이 많습니다.",
    )
    return settings.model_dump()


def player_is_in_any_room(pid):
    return any(
        any(player.id == pid and not player.departed for player in room.players)
        for room in rooms.values()
    )
