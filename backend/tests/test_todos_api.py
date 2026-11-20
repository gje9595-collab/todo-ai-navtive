"""`/api/todos` API 테스트. 테스트 이름 앞의 ID는 docs/acceptance-criteria.md 기준입니다."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from tests.conftest import USER_A, USER_B, assert_error

# ---------- 기본 ----------


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_uses_common_error_format(client: TestClient) -> None:
    assert_error(client.get("/api/unknown", headers=USER_A), 404, "NOT_FOUND")


def test_method_not_allowed_uses_common_error_format(client: TestClient) -> None:
    assert_error(client.put("/api/todos", headers=USER_A), 405, "METHOD_NOT_ALLOWED")


def _post_raw(client: TestClient, raw: bytes):
    headers = {**USER_A, "Content-Type": "application/json"}
    return client.post("/api/todos", content=raw, headers=headers)


def test_malformed_json_returns_422(client: TestClient) -> None:
    error = assert_error(_post_raw(client, b'{"text": '), 422, "VALIDATION_ERROR")
    assert error["message"] == "요청 본문이 올바른 JSON 형식이 아닙니다."


def test_non_utf8_body_returns_400(client: TestClient) -> None:
    # Windows 셸에서 한글이 CP949로 전송되는 경우 등
    assert_error(_post_raw(client, b'{"text": "\xb0\xa1"}'), 400, "BAD_REQUEST")


# ---------- FR-007 / NFR-004: 인증 ----------

ENDPOINTS = [
    ("GET", "/api/todos", None),
    ("POST", "/api/todos", {"text": "할 일"}),
    ("PATCH", f"/api/todos/{uuid4()}", {"completed": True}),
    ("DELETE", f"/api/todos/{uuid4()}", None),
]


@pytest.mark.parametrize(("method", "url", "body"), ENDPOINTS)
def test_ac_fr_007_1_missing_token_returns_401(client: TestClient, method, url, body) -> None:
    response = client.request(method, url, json=body)
    assert_error(response, 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("header", ["user-a", "Basic user-a", "Bearer ", "Bearer"])
def test_malformed_authorization_header_returns_401(client: TestClient, header: str) -> None:
    response = client.get("/api/todos", headers={"Authorization": header})
    assert_error(response, 401, "UNAUTHENTICATED")


def test_ac_nfr_004_2_auth_checked_before_body_validation(client: TestClient) -> None:
    # 본문이 잘못됐어도 인증이 먼저 실패해야 합니다.
    response = client.post("/api/todos", json={"text": "   "})
    assert_error(response, 401, "UNAUTHENTICATED")


# ---------- FR-001: 생성 ----------


def test_ac_fr_001_1_create_todo(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": "  API 명세 초안 작성  "}, headers=USER_A)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "text", "completed", "created_at", "updated_at"}
    UUID(body["id"])
    assert body["text"] == "API 명세 초안 작성"  # 앞뒤 공백 제거
    assert body["completed"] is False
    assert body["created_at"] == body["updated_at"]


def test_create_ignores_completed_in_request(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": "할 일", "completed": True}, headers=USER_A)
    assert response.status_code == 201
    assert response.json()["completed"] is False


# ---------- FR-010: 서버 측 입력 검증 ----------


@pytest.mark.parametrize("text", ["", "   ", "\t\n "])
def test_ac_fr_010_1_blank_text_rejected_on_create(client: TestClient, text: str) -> None:
    error = assert_error(
        client.post("/api/todos", json={"text": text}, headers=USER_A), 422, "VALIDATION_ERROR"
    )
    assert error["message"] == "할 일 내용을 입력해 주세요."
    assert client.get("/api/todos", headers=USER_A).json() == {"items": []}


def test_ac_fr_010_2_text_over_500_chars_rejected(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": "가" * 501}, headers=USER_A)
    error = assert_error(response, 422, "VALIDATION_ERROR")
    assert "500자" in error["message"]


def test_text_of_exactly_500_chars_after_trim_is_accepted(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": f"  {'가' * 500}  "}, headers=USER_A)
    assert response.status_code == 201
    assert len(response.json()["text"]) == 500


@pytest.mark.parametrize("body", [{}, {"text": 123}, {"text": None}, None])
def test_create_with_invalid_body_returns_422(client: TestClient, body) -> None:
    assert_error(client.post("/api/todos", json=body, headers=USER_A), 422, "VALIDATION_ERROR")


# ---------- FR-002: 목록 조회 ----------


def test_ac_fr_002_2_empty_list(client: TestClient) -> None:
    response = client.get("/api/todos", headers=USER_A)
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_ac_fr_002_1_list_in_creation_order(client: TestClient, create_todo) -> None:
    ids = [create_todo(text)["id"] for text in ["첫째", "둘째", "셋째"]]

    items = client.get("/api/todos", headers=USER_A).json()["items"]

    assert [item["id"] for item in items] == ids
    assert [item["text"] for item in items] == ["첫째", "둘째", "셋째"]


# ---------- FR-003 / FR-004: 수정 ----------


def test_ac_fr_003_toggle_completed(client: TestClient, create_todo) -> None:
    todo = create_todo("토글할 일")

    done = client.patch(f"/api/todos/{todo['id']}", json={"completed": True}, headers=USER_A)
    assert done.status_code == 200
    assert done.json()["completed"] is True
    assert done.json()["text"] == "토글할 일"

    undone = client.patch(f"/api/todos/{todo['id']}", json={"completed": False}, headers=USER_A)
    assert undone.json()["completed"] is False


def test_ac_fr_004_2_update_text(client: TestClient, create_todo) -> None:
    todo = create_todo("원래 내용")

    response = client.patch(f"/api/todos/{todo['id']}", json={"text": "  바뀐 내용 "}, headers=USER_A)

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "바뀐 내용"
    assert body["completed"] is False
    assert body["created_at"] == todo["created_at"]
    assert body["updated_at"] >= todo["updated_at"]
    # 목록에도 반영되어야 합니다.
    assert client.get("/api/todos", headers=USER_A).json()["items"][0]["text"] == "바뀐 내용"


def test_update_text_and_completed_together(client: TestClient, create_todo) -> None:
    todo = create_todo("할 일")
    response = client.patch(
        f"/api/todos/{todo['id']}", json={"text": "새 내용", "completed": True}, headers=USER_A
    )
    assert response.json()["text"] == "새 내용"
    assert response.json()["completed"] is True


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"text": None, "completed": None},
        {"text": "   "},
        {"text": "가" * 501},
        {"completed": "yes"},
        {"completed": 1},
    ],
)
def test_update_with_invalid_body_returns_422(client: TestClient, create_todo, body) -> None:
    todo = create_todo("원래 내용")

    response = client.patch(f"/api/todos/{todo['id']}", json=body, headers=USER_A)

    assert_error(response, 422, "VALIDATION_ERROR")
    item = client.get("/api/todos", headers=USER_A).json()["items"][0]
    assert item["text"] == "원래 내용"
    assert item["completed"] is False


def test_update_nonexistent_todo_returns_404(client: TestClient) -> None:
    response = client.patch(f"/api/todos/{uuid4()}", json={"completed": True}, headers=USER_A)
    assert_error(response, 404, "NOT_FOUND")


def test_invalid_uuid_path_returns_422(client: TestClient) -> None:
    response = client.patch("/api/todos/not-a-uuid", json={"completed": True}, headers=USER_A)
    assert_error(response, 422, "VALIDATION_ERROR")


# ---------- FR-005: 삭제 ----------


def test_ac_fr_005_1_delete_todo(client: TestClient, create_todo) -> None:
    keep = create_todo("남길 일")
    remove = create_todo("지울 일")

    response = client.delete(f"/api/todos/{remove['id']}", headers=USER_A)

    assert response.status_code == 204
    assert response.content == b""
    items = client.get("/api/todos", headers=USER_A).json()["items"]
    assert [item["id"] for item in items] == [keep["id"]]


def test_ac_fr_005_2_delete_twice_returns_404(client: TestClient, create_todo) -> None:
    todo = create_todo("지울 일")
    assert client.delete(f"/api/todos/{todo['id']}", headers=USER_A).status_code == 204

    assert_error(client.delete(f"/api/todos/{todo['id']}", headers=USER_A), 404, "NOT_FOUND")


# ---------- FR-008: 사용자별 데이터 격리 ----------


def test_ac_fr_008_1_list_excludes_other_users_todos(client: TestClient, create_todo) -> None:
    create_todo("A의 할 일", USER_A)
    b_todo = create_todo("B의 할 일", USER_B)

    a_items = client.get("/api/todos", headers=USER_A).json()["items"]
    b_items = client.get("/api/todos", headers=USER_B).json()["items"]

    assert [item["text"] for item in a_items] == ["A의 할 일"]
    assert [item["id"] for item in b_items] == [b_todo["id"]]


def test_ac_fr_008_2_cannot_update_other_users_todo(client: TestClient, create_todo) -> None:
    b_todo = create_todo("B의 할 일", USER_B)

    response = client.patch(
        f"/api/todos/{b_todo['id']}", json={"text": "A가 바꿈", "completed": True}, headers=USER_A
    )

    assert_error(response, 403, "FORBIDDEN")
    item = client.get("/api/todos", headers=USER_B).json()["items"][0]
    assert item == b_todo  # B의 데이터는 그대로


def test_ac_fr_008_2_cannot_delete_other_users_todo(client: TestClient, create_todo) -> None:
    b_todo = create_todo("B의 할 일", USER_B)

    assert_error(client.delete(f"/api/todos/{b_todo['id']}", headers=USER_A), 403, "FORBIDDEN")
    assert client.get("/api/todos", headers=USER_B).json()["items"] == [b_todo]


# ---------- 기타 ----------


def test_cors_preflight_allows_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/api/todos",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_crud_flow_end_to_end(client: TestClient) -> None:
    created = client.post("/api/todos", json={"text": "흐름 테스트"}, headers=USER_A).json()
    todo_url = f"/api/todos/{created['id']}"

    client.patch(todo_url, json={"completed": True}, headers=USER_A)
    client.patch(todo_url, json={"text": "흐름 테스트 (수정)"}, headers=USER_A)
    items = client.get("/api/todos", headers=USER_A).json()["items"]
    assert len(items) == 1
    assert items[0]["text"] == "흐름 테스트 (수정)"
    assert items[0]["completed"] is True

    assert client.delete(todo_url, headers=USER_A).status_code == 204
    assert client.get("/api/todos", headers=USER_A).json() == {"items": []}
