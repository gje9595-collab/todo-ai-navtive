"""요청/응답 스키마 (API 명세 2-2, 3절)."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, StrictBool, StrictStr, field_validator, model_validator

from app.models.todo import Todo

TEXT_MAX_LENGTH = 500


def normalize_text(value: str) -> str:
    """앞뒤 공백을 제거하고 1~500자인지 검사합니다 (FR-010)."""
    text = value.strip()
    if not text:
        raise ValueError("할 일 내용을 입력해 주세요.")
    if len(text) > TEXT_MAX_LENGTH:
        raise ValueError(f"할 일은 {TEXT_MAX_LENGTH}자 이하로 입력해 주세요.")
    return text


class TodoCreateRequest(BaseModel):
    text: StrictStr

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return normalize_text(value)


class TodoUpdateRequest(BaseModel):
    """부분 업데이트. `text`, `completed` 중 최소 1개가 필요합니다."""

    text: StrictStr | None = None
    completed: StrictBool | None = None

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str | None) -> str | None:
        return None if value is None else normalize_text(value)

    @model_validator(mode="after")
    def _require_any_field(self) -> Self:
        if self.text is None and self.completed is None:
            raise ValueError("수정할 항목(text 또는 completed)을 하나 이상 보내 주세요.")
        return self


class TodoResponse(BaseModel):
    id: UUID
    text: str
    completed: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, todo: Todo) -> "TodoResponse":
        return cls(
            id=todo.id,
            text=todo.text,
            completed=todo.completed,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )


class TodoListResponse(BaseModel):
    items: list[TodoResponse]
