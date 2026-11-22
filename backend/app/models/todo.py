"""저장소에 보관되는 ToDo 도메인 모델."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, get_args
from uuid import UUID

# 고정 카테고리 3종 (FR-013, PRD D-9). DB의 todos_category_valid 제약과 같은 값이다.
Category = Literal["work", "personal", "study"]
CATEGORIES: tuple[str, ...] = get_args(Category)
DEFAULT_CATEGORY: Category = "personal"


@dataclass(frozen=True)
class Todo:
    """불변 객체. 수정할 때는 `dataclasses.replace`로 새 객체를 만든다."""

    id: UUID
    # 1~2단계는 dev 토큰 문자열, 3단계부터 Supabase Auth 사용자 UUID 문자열 (PRD D-3)
    user_id: str
    text: str
    completed: bool
    created_at: datetime
    updated_at: datetime
    # 마감일. 시각 없이 날짜만 저장하고, 없으면 None (FR-012, PRD D-8)
    due_date: date | None = None
    # 카테고리. 항상 값이 있고 기본은 personal (FR-013)
    category: Category = DEFAULT_CATEGORY
