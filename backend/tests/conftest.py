"""API 테스트 공용 fixture. 테스트마다 빈 In-Memory 저장소를 가진 새 앱을 만든다."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.dependencies import get_todo_service
from app.main import create_app
from app.services.todo_service import TodoService

USER_A = {"Authorization": "Bearer user-a"}
USER_B = {"Authorization": "Bearer user-b"}
FRONTEND_ORIGIN = "http://localhost:5173"


@pytest.fixture
def app() -> FastAPI:
    return create_app(Settings(cors_origins=(FRONTEND_ORIGIN,)))


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


class FakeClock:
    """호출할 때마다 1초씩 증가하는 시계. 시각 비교를 결정적으로 만든다."""

    def __init__(self, start: datetime = datetime(2026, 11, 20, 5, 0, tzinfo=UTC)) -> None:
        self.now = start

    def __call__(self) -> datetime:
        current = self.now
        self.now += timedelta(seconds=1)
        return current


@pytest.fixture
def clock(app: FastAPI) -> FakeClock:
    """Service에 가짜 시계를 주입한다 (CLAUDE.md 8-1: 테스트용 clock 주입)."""
    fake = FakeClock()
    app.dependency_overrides[get_todo_service] = lambda: TodoService(app.state.todo_repository, clock=fake)
    return fake


@pytest.fixture
def create_todo(client: TestClient) -> Callable[..., dict[str, Any]]:
    """할 일을 만들고 응답 본문을 돌려주는 헬퍼."""

    def _create(text: str, headers: dict[str, str] = USER_A) -> dict[str, Any]:
        response = client.post("/api/todos", json={"text": text}, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


def assert_error(response: Any, status_code: int, code: str) -> dict[str, Any]:
    """공통 에러 포맷(API 명세 2-1)을 검사하고 error 객체를 돌려준다 (AC-NFR-006-1)."""
    assert response.status_code == status_code, response.text
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == {"code", "message", "details"}
    assert error["code"] == code
    assert isinstance(error["message"], str) and error["message"]
    return error
