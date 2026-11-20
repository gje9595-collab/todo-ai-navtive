"""`/api/todos` 엔드포인트 (API 명세 3절). HTTP 입출력 변환만 담당합니다."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.auth import CurrentUserId
from app.dependencies import TodoServiceDep
from app.schemas.todo import (
    TodoCreateRequest,
    TodoListResponse,
    TodoResponse,
    TodoUpdateRequest,
)

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=TodoListResponse)
def list_todos(user_id: CurrentUserId, service: TodoServiceDep) -> TodoListResponse:
    todos = service.list_todos(user_id)
    return TodoListResponse(items=[TodoResponse.from_model(todo) for todo in todos])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    body: TodoCreateRequest, user_id: CurrentUserId, service: TodoServiceDep
) -> TodoResponse:
    return TodoResponse.from_model(service.create_todo(user_id, body.text))


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: UUID, body: TodoUpdateRequest, user_id: CurrentUserId, service: TodoServiceDep
) -> TodoResponse:
    todo = service.update_todo(user_id, todo_id, text=body.text, completed=body.completed)
    return TodoResponse.from_model(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: UUID, user_id: CurrentUserId, service: TodoServiceDep) -> Response:
    service.delete_todo(user_id, todo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
