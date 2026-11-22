"""`/api/todos` 엔드포인트 (API 명세 3-2~3-5절). HTTP 입출력 변환만 담당하고 규칙은 Service에 둔다."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.core.auth import CurrentUserId
from app.dependencies import TodoServiceDep
from app.schemas.todo import (
    CategoryField,
    TodoCreateRequest,
    TodoListResponse,
    TodoResponse,
    TodoUpdateRequest,
)
from app.services.todo_service import UNSET

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=TodoListResponse)
def list_todos(
    user_id: CurrentUserId,
    service: TodoServiceDep,
    category: Annotated[CategoryField | None, Query(description="work | personal | study. 생략하면 전체")] = None,
) -> TodoListResponse:
    """본인 소유 할 일을 생성 순서로 반환한다. `category`로 거를 수 있다 (FR-002, FR-008, FR-014)."""
    todos = service.list_todos(user_id, category)
    return TodoListResponse(items=[TodoResponse.from_model(todo) for todo in todos])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(user_id: CurrentUserId, body: TodoCreateRequest, service: TodoServiceDep) -> TodoResponse:
    """할 일을 만든다. 마감일은 선택, 카테고리는 기본 personal (FR-001, FR-010, FR-012, FR-013)."""
    return TodoResponse.from_model(service.create_todo(user_id, body.text, body.due_date, body.category))


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: UUID, user_id: CurrentUserId, body: TodoUpdateRequest, service: TodoServiceDep
) -> TodoResponse:
    """텍스트, 완료 상태, 마감일, 카테고리를 바꾼다 (FR-003, FR-004, FR-008, FR-012, FR-013)."""
    todo = service.update_todo(
        user_id,
        todo_id,
        text=body.text,
        completed=body.completed,
        # 본문에 due_date가 없으면 기존 마감일을 유지한다 (AC-FR-012-3).
        due_date=body.due_date if body.has_due_date else UNSET,
        category=body.category,
    )
    return TodoResponse.from_model(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: UUID, user_id: CurrentUserId, service: TodoServiceDep) -> Response:
    """할 일을 삭제한다. 두 번째 삭제는 404 (FR-005, AC-FR-005-2)."""
    service.delete_todo(user_id, todo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
