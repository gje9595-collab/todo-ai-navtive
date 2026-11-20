"""ToDo 비즈니스 로직: 생성 규칙, 소유권 검사(FR-008), 갱신 시각 관리."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.errors import ForbiddenError, NotFoundError
from app.models.todo import Todo
from app.repositories.todo_repository import TodoRepository


def _utc_now() -> datetime:
    return datetime.now(UTC)


class TodoService:
    def __init__(self, repository: TodoRepository, clock: Callable[[], datetime] = _utc_now) -> None:
        self._repository = repository
        self._clock = clock

    def list_todos(self, user_id: str) -> list[Todo]:
        return self._repository.list_by_user(user_id)

    def create_todo(self, user_id: str, text: str) -> Todo:
        now = self._clock()
        todo = Todo(
            id=uuid4(),
            user_id=user_id,
            text=text,
            completed=False,
            created_at=now,
            updated_at=now,
        )
        return self._repository.add(todo)

    def update_todo(
        self,
        user_id: str,
        todo_id: UUID,
        *,
        text: str | None = None,
        completed: bool | None = None,
    ) -> Todo:
        todo = self._get_owned(user_id, todo_id)
        changes: dict[str, object] = {"updated_at": self._clock()}
        if text is not None:
            changes["text"] = text
        if completed is not None:
            changes["completed"] = completed
        return self._repository.update(replace(todo, **changes))

    def delete_todo(self, user_id: str, todo_id: UUID) -> None:
        self._get_owned(user_id, todo_id)
        self._repository.delete(todo_id)

    def _get_owned(self, user_id: str, todo_id: UUID) -> Todo:
        """존재하지 않으면 404, 다른 사용자 소유면 403을 발생시킵니다."""
        todo = self._repository.get(todo_id)
        if todo is None:
            raise NotFoundError()
        if todo.user_id != user_id:
            raise ForbiddenError()
        return todo
