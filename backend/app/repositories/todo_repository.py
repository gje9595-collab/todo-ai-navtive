"""ToDo 저장소 계층.

`TodoRepository`는 저장소가 지켜야 할 인터페이스이고, 현재 구현은 `InMemoryTodoRepository`입니다.
Supabase 연동 시 같은 인터페이스로 `SupabaseTodoRepository`를 추가해 교체합니다.
서버를 재시작하면 In-Memory 데이터는 사라집니다.
"""

from threading import Lock
from typing import Protocol
from uuid import UUID

from app.models.todo import Todo


class TodoRepository(Protocol):
    def list_by_user(self, user_id: str) -> list[Todo]:
        """user_id 소유 ToDo를 생성 순서(오름차순)로 반환합니다."""
        ...

    def get(self, todo_id: UUID) -> Todo | None:
        """소유자와 관계없이 id로 조회합니다. 소유권 판단은 Service가 합니다."""
        ...

    def add(self, todo: Todo) -> Todo: ...

    def update(self, todo: Todo) -> Todo: ...

    def delete(self, todo_id: UUID) -> None: ...


class InMemoryTodoRepository:
    """프로세스 메모리에 ToDo를 보관하는 저장소. dict의 삽입 순서가 생성 순서입니다."""

    def __init__(self) -> None:
        self._items: dict[UUID, Todo] = {}
        self._lock = Lock()

    def list_by_user(self, user_id: str) -> list[Todo]:
        with self._lock:
            return [todo for todo in self._items.values() if todo.user_id == user_id]

    def get(self, todo_id: UUID) -> Todo | None:
        with self._lock:
            return self._items.get(todo_id)

    def add(self, todo: Todo) -> Todo:
        with self._lock:
            self._items[todo.id] = todo
            return todo

    def update(self, todo: Todo) -> Todo:
        with self._lock:
            if todo.id not in self._items:
                raise KeyError(todo.id)
            self._items[todo.id] = todo
            return todo

    def delete(self, todo_id: UUID) -> None:
        with self._lock:
            self._items.pop(todo_id, None)
