"""HTTP 요청 스키마."""
from pydantic import BaseModel, ConfigDict, Field


class Guest(BaseModel):
    name: str = Field(min_length=1, max_length=16)


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capacity: int = Field(default=10, ge=5, le=10)
    roles: list[str] = Field(default_factory=lambda: ["percival", "morgana"])
    lady: bool = False
    discussion_seconds: int = Field(default=180, ge=30, le=600)
    vote_seconds: int = Field(default=60, ge=15, le=180)
    reconnect_seconds: int = Field(default=30, ge=0, le=120)


class CreateRoom(BaseModel):
    title: str = Field(min_length=1, max_length=40)
    password: str = Field(default="", max_length=64)
    settings: Settings = Field(default_factory=Settings)


class JoinRoom(BaseModel):
    password: str = Field(default="", max_length=64)
