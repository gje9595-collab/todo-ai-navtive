"""ToDo 비즈니스 규칙: 생성 규칙, 소유권 검사(FR-008), 갱신 시각 관리."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from enum import Enum
from uuid import UUID, uuid4

from app.core.errors import ForbiddenError, NotFoundError
from app.models.todo import DEFAULT_CATEGORY, Category, Todo
from app.repositories.todo_repository import TodoRepository


class Unset(Enum):
    """"값을 보내지 않음"을 나타낸다. 마감일은 `None`이 "지우기"라서 생략과 구분해야 한다 (FR-012)."""

    UNSET = "unset"


UNSET = Unset.UNSET


def _utc_now() -> datetime:
    return datetime.now(UTC)


class TodoService:
    """`clock`을 주입할 수 있어 테스트에서 시각을 고정할 수 있다."""

    def __init__(self, repository: TodoRepository, clock: Callable[[], datetime] = _utc_now) -> None:
        self._repository = repository
        self._clock = clock

    def list_todos(self, user_id: str, category: Category | None = None) -> list[Todo]:
        """본인 할 일 목록. `category`를 주면 그 카테고리만 반환한다 (FR-002, FR-014)."""
        return self._repository.list_by_user(user_id, category)

    def create_todo(
        self,
        user_id: str,
        text: str,
        due_date: date | None = None,
        category: Category = DEFAULT_CATEGORY,
    ) -> Todo:
        """새 할 일은 항상 미완료이고, created_at과 updated_at이 같다 (AC-FR-001-3, FR-012, FR-013)."""
        now = self._clock()
        todo = Todo(
            id=uuid4(),
            user_id=user_id,
            text=text,
            completed=False,
            created_at=now,
            updated_at=now,
            due_date=due_date,
            category=category,
        )
        return self._repository.add(todo)

    def update_todo(
        self,
        user_id: str,
        todo_id: UUID,
        *,
        text: str | None = None,
        completed: bool | None = None,
        due_date: date | None | Unset = UNSET,
        category: Category | None = None,
    ) -> Todo:
        """주어진 필드만 바꾼다. 값이 같아도 요청이 성공하면 updated_at을 갱신한다 (api-spec 3-4).

        `due_date`는 `UNSET`이면 유지하고, `None`이면 지운다 (AC-FR-012-2/3).
        `category`는 `None`이면 유지한다 (AC-FR-013-2).
        """
        todo = self._get_owned(user_id, todo_id)
        changes: dict[str, object] = {"updated_at": self._clock()}
        if text is not None:
            changes["text"] = text
        if completed is not None:
            changes["completed"] = completed
        if due_date is not UNSET:
            changes["due_date"] = due_date
        if category is not None:
            changes["category"] = category
        return self._repository.update(replace(todo, **changes))

    def delete_todo(self, user_id: str, todo_id: UUID) -> None:
        self._get_owned(user_id, todo_id)
        self._repository.delete(todo_id, user_id)

    def _get_owned(self, user_id: str, todo_id: UUID) -> Todo:
        """없으면 404, 다른 사용자 소유면 403 (PRD D-6, AC-FR-008-2/3)."""
        todo = self._repository.get(todo_id)
        if todo is None:
            raise NotFoundError()
        if todo.user_id != user_id:
            raise ForbiddenError()
        return todo
