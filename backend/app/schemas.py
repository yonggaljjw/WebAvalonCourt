"""HTTP 요청 본문의 형식과 범위를 정의하는 Pydantic 스키마."""

from pydantic import BaseModel, ConfigDict, Field


class Guest(BaseModel):
    """게스트 입장 시 받는 닉네임."""

    name: str = Field(min_length=1, max_length=16)


class Settings(BaseModel):
    """방장이 설정할 수 있는 게임 옵션."""

    # 정의되지 않은 필드가 들어오면 조용히 버리지 않고 요청 오류로 처리합니다.
    model_config = ConfigDict(extra="forbid")

    capacity: int = Field(default=10, ge=5, le=10)
    roles: list[str] = Field(default_factory=lambda: ["percival", "morgana"])
    lady: bool = False
    discussion_seconds: int = Field(default=180, ge=30, le=600)
    vote_seconds: int = Field(default=60, ge=15, le=180)
    reconnect_seconds: int = Field(default=30, ge=0, le=120)


class CreateRoom(BaseModel):
    """방 생성 요청."""

    title: str = Field(min_length=1, max_length=40)
    password: str = Field(default="", max_length=64)
    # 요청에 settings가 없어도 기본 Settings 객체를 새로 만들어 사용합니다.
    settings: Settings = Field(default_factory=Settings)


class JoinRoom(BaseModel):
    """방 입장 시 필요한 비밀번호. 공개방이면 빈 문자열입니다."""

    password: str = Field(default="", max_length=64)
