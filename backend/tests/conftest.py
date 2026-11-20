"""API 테스트 공용 fixture. 테스트마다 빈 In-Memory 저장소를 가진 새 앱을 만듭니다."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

USER_A = {"Authorization": "Bearer user-a"}
USER_B = {"Authorization": "Bearer user-b"}


@pytest.fixture
def client() -> TestClient:
    app = create_app(Settings(cors_origins=("http://localhost:5173",)))
    return TestClient(app)


@pytest.fixture
def create_todo(client: TestClient) -> Callable[..., dict[str, Any]]:
    """할 일을 만들고 응답 본문을 돌려주는 헬퍼."""

    def _create(text: str, headers: dict[str, str] = USER_A) -> dict[str, Any]:
        response = client.post("/api/todos", json={"text": text}, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


def assert_error(response: Any, status_code: int, code: str) -> dict[str, Any]:
    """공통 에러 포맷(API 명세 2-1)을 검사하고 error 객체를 돌려줍니다."""
    assert response.status_code == status_code, response.text
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert error["code"] == code
    assert isinstance(error["message"], str) and error["message"]
    assert "details" in error
    return error
