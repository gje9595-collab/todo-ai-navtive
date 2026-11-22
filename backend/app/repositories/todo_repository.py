"""ToDo 저장소 계층.

`TodoRepository`는 저장소가 지켜야 할 인터페이스(Protocol)이고, 1단계 구현은 `InMemoryTodoRepository`다.
2단계(T-23)에서 같은 인터페이스로 `SupabaseTodoRepository`를 추가한다.
In-Memory 데이터는 서버를 재시작하면 사라진다.
"""

from threading import Lock
from typing import Protocol
from uuid import UUID

from app.models.todo import Category, Todo


class TodoRepository(Protocol):
    def list_by_user(self, user_id: str, category: Category | None = None) -> list[Todo]:
        """user_id 소유 ToDo를 생성 순서(created_at 오름차순)로 반환한다 (FR-002).

        `category`가 있으면 그 카테고리만 반환한다. 소유자 조건은 항상 함께 건다 (FR-014, FR-008).
        """
        ...

    def get(self, todo_id: UUID) -> Todo | None:
        """소유자와 관계없이 id로 조회한다. 소유권(403/404) 판단은 Service가 한다."""
        ...

    def add(self, todo: Todo) -> Todo: ...

    def update(self, todo: Todo) -> Todo:
        """`todo.id`와 `todo.user_id`가 모두 일치하는 행만 갱신한다 (api-spec 3-4)."""
        ...

    def delete(self, todo_id: UUID, user_id: str) -> None:
        """`todo_id`와 `user_id`가 모두 일치하는 행만 삭제한다 (api-spec 3-5)."""
        ...


class InMemoryTodoRepository:
    """프로세스 메모리에 ToDo를 보관하는 저장소. 요청 스레드가 여럿일 수 있어 Lock으로 보호한다."""

    def __init__(self) -> None:
        self._items: dict[UUID, Todo] = {}
        self._lock = Lock()

    def list_by_user(self, user_id: str, category: Category | None = None) -> list[Todo]:
        with self._lock:
            owned = [
                todo
                for todo in self._items.values()
                if todo.user_id == user_id and (category is None or todo.category == category)
            ]
        # 안정 정렬이므로 created_at이 같으면 삽입(생성) 순서가 유지된다.
        return sorted(owned, key=lambda todo: todo.created_at)

    def get(self, todo_id: UUID) -> Todo | None:
        with self._lock:
            return self._items.get(todo_id)

    def add(self, todo: Todo) -> Todo:
        with self._lock:
            self._items[todo.id] = todo
            return todo

    def update(self, todo: Todo) -> Todo:
        with self._lock:
            current = self._items.get(todo.id)
            if current is None or current.user_id != todo.user_id:
                raise KeyError(todo.id)
            self._items[todo.id] = todo
            return todo

    def delete(self, todo_id: UUID, user_id: str) -> None:
        with self._lock:
            current = self._items.get(todo_id)
            if current is not None and current.user_id == user_id:
                del self._items[todo_id]
