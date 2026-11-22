"""계층 간 의존성 연결. 저장소는 앱 인스턴스마다 하나씩(`app.state`) 둔다."""

from typing import Annotated

from fastapi import Depends, Request

from app.repositories.todo_repository import TodoRepository
from app.services.todo_service import TodoService


def get_todo_repository(request: Request) -> TodoRepository:
    return request.app.state.todo_repository


def get_todo_service(repository: Annotated[TodoRepository, Depends(get_todo_repository)]) -> TodoService:
    return TodoService(repository)


TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]
