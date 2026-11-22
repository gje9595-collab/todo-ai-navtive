"""요청·응답 스키마 (API 명세 2-2, 2-3, 2-4, 2-5, 3절)."""

import re
from datetime import date, datetime
from typing import Annotated, Any, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StrictBool,
    StrictStr,
    field_validator,
    model_validator,
)

from app.models.todo import CATEGORIES, DEFAULT_CATEGORY, Category, Todo

TEXT_MAX_LENGTH = 500


def normalize_text(value: str) -> str:
    """앞뒤 공백(탭·줄바꿈 포함)을 제거하고 1~500자인지 검사한다 (FR-010, api-spec 2-3).

    글자 수는 유니코드 코드 포인트 기준(Python `len`)이다.
    """
    text = value.strip()
    if not text:
        raise ValueError("할 일 내용을 입력해 주세요.")
    if len(text) > TEXT_MAX_LENGTH:
        raise ValueError(f"할 일은 {TEXT_MAX_LENGTH}자 이하로 입력해 주세요.")
    return text


DUE_DATE_MIN = date(2000, 1, 1)
DUE_DATE_MAX = date(2100, 12, 31)
# `\d`는 유니코드 숫자(예: 전각 숫자)도 받으므로 [0-9]로 제한한다.
_DUE_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_due_date(value: Any) -> date | None:
    """마감일을 `YYYY-MM-DD` 문자열로만 받아 date로 바꾼다 (FR-012, api-spec 2-4).

    `date.fromisoformat`은 `20261125`나 시각이 붙은 값도 받아들이므로 형식을 먼저 검사한다.
    숫자 등 문자열이 아닌 값도 형식 오류로 거부한다. `None`은 마감일 없음이다.
    """
    if value is None:
        return None
    if not isinstance(value, str) or not _DUE_DATE_PATTERN.fullmatch(value):
        raise ValueError("마감일은 YYYY-MM-DD 형식이어야 합니다.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError("존재하지 않는 날짜입니다.") from None
    if not DUE_DATE_MIN <= parsed <= DUE_DATE_MAX:
        raise ValueError("마감일은 2000-01-01부터 2100-12-31 사이여야 합니다.")
    return parsed


def parse_category(value: Any) -> str:
    """카테고리는 허용값 문자열과 정확히 일치해야 한다 (FR-013, api-spec 2-5).

    `Literal` 기본 오류 대신 한국어 메시지를 주려고 직접 검사한다. `None`, 숫자, 대소문자 변형도 거부한다.
    """
    if not isinstance(value, str) or value not in CATEGORIES:
        raise ValueError(f"카테고리는 {', '.join(CATEGORIES)} 중 하나여야 합니다.")
    return value


# 요청 본문과 목록 쿼리 파라미터(FR-014)에 같은 검증을 쓴다.
CategoryField = Annotated[Category, BeforeValidator(parse_category)]


class _StrictRequest(BaseModel):
    """정의되지 않은 필드는 422로 거부한다 (AC-FR-010-4)."""

    model_config = ConfigDict(extra="forbid")


class TodoCreateRequest(_StrictRequest):
    text: StrictStr
    # 생략하거나 null이면 마감일 없음 (AC-FR-012-1)
    due_date: date | None = None
    # 생략하면 personal. null은 422 (AC-FR-013-1/3)
    category: CategoryField = DEFAULT_CATEGORY

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return normalize_text(value)

    @field_validator("due_date", mode="before")
    @classmethod
    def _validate_due_date(cls, value: Any) -> date | None:
        return parse_due_date(value)


class TodoUpdateRequest(_StrictRequest):
    """부분 수정. `text`, `completed`, `due_date`, `category` 중 최소 하나가 필요하다.

    `text`, `completed`, `category`의 `null`은 거부한다. `due_date`만 `null`을 허용하며 마감일을 지운다는 뜻이다.
    `due_date`를 생략했는지는 `model_fields_set`으로 구분한다 (api-spec 3-4, AC-FR-012-2/3).
    """

    text: StrictStr | None = None
    completed: StrictBool | None = None
    due_date: date | None = None
    category: CategoryField | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_null(cls, data: Any) -> Any:
        # 필드를 생략한 것과 null을 보낸 것을 구분한다. null은 의도가 모호하므로 거부한다 (api-spec 3-4).
        if isinstance(data, dict):
            nullable_forbidden = ("text", "completed", "category")
            null_fields = [key for key in nullable_forbidden if key in data and data[key] is None]
            if null_fields:
                raise ValueError(f"{', '.join(null_fields)}에는 null을 보낼 수 없습니다.")
        return data

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str | None) -> str | None:
        return None if value is None else normalize_text(value)

    @field_validator("due_date", mode="before")
    @classmethod
    def _validate_due_date(cls, value: Any) -> date | None:
        return parse_due_date(value)

    @property
    def has_due_date(self) -> bool:
        """요청 본문에 `due_date`가 있었는지. 값이 `None`이면 마감일을 지운다."""
        return "due_date" in self.model_fields_set

    @model_validator(mode="after")
    def _require_any_field(self) -> Self:
        if self.text is None and self.completed is None and self.category is None and not self.has_due_date:
            raise ValueError("수정할 항목(text, completed, due_date, category)을 하나 이상 보내 주세요.")
        return self


class TodoResponse(BaseModel):
    """응답에는 user_id를 넣지 않는다 (AC-FR-002-4)."""

    id: UUID
    text: str
    completed: bool
    # `YYYY-MM-DD` 또는 null (FR-012)
    due_date: date | None
    # work | personal | study (FR-013)
    category: Category
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, todo: Todo) -> "TodoResponse":
        return cls(
            id=todo.id,
            text=todo.text,
            completed=todo.completed,
            due_date=todo.due_date,
            category=todo.category,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )


class TodoListResponse(BaseModel):
    items: list[TodoResponse]


class HealthResponse(BaseModel):
    status: str
