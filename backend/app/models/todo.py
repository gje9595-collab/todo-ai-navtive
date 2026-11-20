"""저장소에 보관되는 ToDo 도메인 모델."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Todo:
    id: UUID
    user_id: str
    text: str
    completed: bool
    created_at: datetime
    updated_at: datetime
