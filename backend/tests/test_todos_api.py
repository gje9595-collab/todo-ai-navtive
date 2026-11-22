"""ToDo API 테스트. 함수 이름은 수용 기준 ID로 시작한다 (docs/acceptance-criteria.md).

예: `pytest -k ac_fr_008` → FR-008(소유자 격리) 기준만 실행
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.dependencies import get_todo_repository
from app.main import create_app
from tests.conftest import FRONTEND_ORIGIN, USER_A, USER_B, assert_error

MISSING_ID = "00000000-0000-4000-8000-000000000000"


# ───────── FR-001 할 일 추가 ─────────


def test_ac_fr_001_3_create_trims_text_and_starts_incomplete(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": "  운동  "}, headers=USER_A)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "text", "completed", "due_date", "category", "created_at", "updated_at"}
    assert body["text"] == "운동"
    assert body["completed"] is False
    assert body["created_at"] == body["updated_at"]


# ───────── FR-002 목록 조회 ─────────


def test_ac_fr_002_1_list_in_creation_order(client: TestClient, create_todo) -> None:
    for text in ("a", "b", "c"):
        create_todo(text)

    response = client.get("/api/todos", headers=USER_A)

    assert response.status_code == 200
    assert [item["text"] for item in response.json()["items"]] == ["a", "b", "c"]


def test_ac_fr_002_1_list_order_with_fixed_clock(client: TestClient, clock, create_todo) -> None:
    # 시각이 결정적인 경우에도 생성 순서대로 반환되는지 확인한다.
    for text in ("first", "second", "third"):
        create_todo(text)

    items = client.get("/api/todos", headers=USER_A).json()["items"]

    assert [item["text"] for item in items] == ["first", "second", "third"]
    assert items[0]["created_at"] < items[1]["created_at"] < items[2]["created_at"]


def test_ac_fr_002_2_empty_list(client: TestClient) -> None:
    response = client.get("/api/todos", headers=USER_A)

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_ac_fr_002_4_response_has_no_user_id(client: TestClient, create_todo) -> None:
    created = create_todo("비밀")
    listed = client.get("/api/todos", headers=USER_A).json()["items"][0]

    assert "user_id" not in created
    assert "user_id" not in listed


# ───────── FR-003 완료 토글 ─────────


def test_ac_fr_003_2_toggle_completed_back_and_forth(client: TestClient, create_todo) -> None:
    todo_id = create_todo("치과 예약")["id"]

    done = client.patch(f"/api/todos/{todo_id}", json={"completed": True}, headers=USER_A)
    undone = client.patch(f"/api/todos/{todo_id}", json={"completed": False}, headers=USER_A)

    assert done.status_code == 200 and done.json()["completed"] is True
    assert undone.status_code == 200 and undone.json()["completed"] is False
    assert undone.json()["text"] == "치과 예약"


# ───────── FR-004 텍스트 수정 ─────────


def test_ac_fr_004_6_update_text_moves_updated_at(client: TestClient, clock, create_todo) -> None:
    created = create_todo("초안")

    response = client.patch(f"/api/todos/{created['id']}", json={"text": "  최종안 "}, headers=USER_A)

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "최종안"
    assert body["completed"] is False
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] > body["created_at"]


def test_ac_fr_004_6_update_text_and_completed_together(client: TestClient, create_todo) -> None:
    todo_id = create_todo("보고서")["id"]

    body = client.patch(f"/api/todos/{todo_id}", json={"text": "보고서 제출", "completed": True}, headers=USER_A).json()

    assert (body["text"], body["completed"]) == ("보고서 제출", True)


# ───────── FR-005 삭제 ─────────


def test_ac_fr_005_2_delete_then_delete_again_returns_404(client: TestClient, create_todo) -> None:
    todo_id = create_todo("임시")["id"]

    first = client.delete(f"/api/todos/{todo_id}", headers=USER_A)
    second = client.delete(f"/api/todos/{todo_id}", headers=USER_A)

    assert first.status_code == 204
    assert first.content == b""
    assert_error(second, 404, "NOT_FOUND")
    assert client.get("/api/todos", headers=USER_A).json() == {"items": []}


# ───────── FR-007 인증 ─────────

TODO_ENDPOINTS = [
    ("GET", "/api/todos", None),
    ("POST", "/api/todos", {"text": "x"}),
    ("PATCH", f"/api/todos/{MISSING_ID}", {"completed": True}),
    ("DELETE", f"/api/todos/{MISSING_ID}", None),
]


@pytest.mark.parametrize(("method", "url", "body"), TODO_ENDPOINTS)
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer "}, {"Authorization": "Bearer"}])
def test_ac_fr_007_1_requests_without_valid_bearer_return_401(
    client: TestClient, method: str, url: str, body: Any, headers: dict[str, str]
) -> None:
    response = client.request(method, url, json=body, headers=headers)

    assert_error(response, 401, "UNAUTHENTICATED")


def test_ac_fr_007_1_dev_token_longer_than_128_chars_returns_401(client: TestClient) -> None:
    response = client.get("/api/todos", headers={"Authorization": "Bearer " + "x" * 129})

    assert_error(response, 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("body", [{"text": ""}, {"text": 123}, {}, {"done": True}])
def test_ac_fr_007_2_auth_is_checked_before_body_validation(client: TestClient, body: dict[str, Any]) -> None:
    response = client.post("/api/todos", json=body)

    assert_error(response, 401, "UNAUTHENTICATED")


def test_ac_fr_007_2_auth_is_checked_before_malformed_json(client: TestClient) -> None:
    # FastAPI는 JSON 파싱을 인증보다 먼저 하므로, 에러 처리기에서 인증 우선 규칙을 보장한다.
    response = client.post("/api/todos", content=b'{"text": ', headers={"Content-Type": "application/json"})

    assert_error(response, 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("mode", ["prod", "", "DEV", "supabase"])
def test_ac_fr_007_3_unsupported_auth_mode_fails_app_creation(mode: str) -> None:
    # supabase는 명세상 허용 값이지만 3단계(T-41) 전까지는 구현되지 않아 시작을 막는다.
    with pytest.raises(RuntimeError):
        create_app(Settings(auth_mode=mode))


def test_ac_fr_007_5_health_needs_no_auth(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ───────── FR-008 소유자 격리 ─────────


def test_ac_fr_008_1_list_returns_only_own_todos(client: TestClient, create_todo) -> None:
    create_todo("A의 할 일", headers=USER_A)
    create_todo("B의 할 일", headers=USER_B)

    a_items = client.get("/api/todos", headers=USER_A).json()["items"]
    b_items = client.get("/api/todos", headers=USER_B).json()["items"]

    assert [item["text"] for item in a_items] == ["A의 할 일"]
    assert [item["text"] for item in b_items] == ["B의 할 일"]


def test_ac_fr_008_2_cannot_update_other_users_todo(client: TestClient, create_todo) -> None:
    todo = create_todo("A의 할 일", headers=USER_A)

    response = client.patch(f"/api/todos/{todo['id']}", json={"text": "B가 바꿈", "completed": True}, headers=USER_B)

    assert_error(response, 403, "FORBIDDEN")
    unchanged = client.get("/api/todos", headers=USER_A).json()["items"][0]
    assert (unchanged["text"], unchanged["completed"]) == ("A의 할 일", False)


def test_ac_fr_008_2_cannot_delete_other_users_todo(client: TestClient, create_todo) -> None:
    todo = create_todo("A의 할 일", headers=USER_A)

    response = client.delete(f"/api/todos/{todo['id']}", headers=USER_B)

    assert_error(response, 403, "FORBIDDEN")
    assert len(client.get("/api/todos", headers=USER_A).json()["items"]) == 1


@pytest.mark.parametrize(("method", "body"), [("PATCH", {"completed": True}), ("DELETE", None)])
def test_ac_fr_008_3_missing_todo_returns_404(client: TestClient, method: str, body: Any) -> None:
    response = client.request(method, f"/api/todos/{MISSING_ID}", json=body, headers=USER_A)

    assert_error(response, 404, "NOT_FOUND")


# ───────── FR-010 서버 입력 검증 ─────────


@pytest.mark.parametrize("text", ["", "   ", "\n\t", "　"])
def test_ac_fr_010_1_blank_text_rejected(client: TestClient, create_todo, text: str) -> None:
    created = client.post("/api/todos", json={"text": text}, headers=USER_A)
    todo_id = create_todo("원래 내용")["id"]
    updated = client.patch(f"/api/todos/{todo_id}", json={"text": text}, headers=USER_A)

    for response in (created, updated):
        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert error["message"] == "할 일 내용을 입력해 주세요."
        assert {"field": "text", "message": "할 일 내용을 입력해 주세요."} in error["details"]


def test_ac_fr_010_2_length_limit_is_500_code_points_after_trim(client: TestClient) -> None:
    ok_ascii = client.post("/api/todos", json={"text": "  " + "a" * 500 + "  "}, headers=USER_A)
    ok_emoji = client.post("/api/todos", json={"text": "😀" * 500}, headers=USER_A)
    ok_korean = client.post("/api/todos", json={"text": "가" * 500}, headers=USER_A)
    too_long = client.post("/api/todos", json={"text": "가" * 501}, headers=USER_A)

    assert ok_ascii.status_code == 201
    assert ok_emoji.status_code == 201
    assert ok_korean.status_code == 201
    error = assert_error(too_long, 422, "VALIDATION_ERROR")
    assert error["message"] == "할 일은 500자 이하로 입력해 주세요."


@pytest.mark.parametrize("body", [{"text": 123}, {"text": None}, {"text": ["a"]}, {}])
def test_ac_fr_010_3_create_rejects_non_string_text(client: TestClient, body: dict[str, Any]) -> None:
    error = assert_error(client.post("/api/todos", json=body, headers=USER_A), 422, "VALIDATION_ERROR")

    assert error["details"][0]["field"] == "text"


@pytest.mark.parametrize("body", [{"completed": "true"}, {"completed": 1}, {"text": None}, {"completed": None}])
def test_ac_fr_010_3_update_rejects_wrong_types_and_null(client: TestClient, create_todo, body: dict[str, Any]) -> None:
    todo_id = create_todo("항목")["id"]

    assert_error(client.patch(f"/api/todos/{todo_id}", json=body, headers=USER_A), 422, "VALIDATION_ERROR")


def test_ac_fr_010_4_update_without_fields_returns_422(client: TestClient, create_todo) -> None:
    todo_id = create_todo("항목")["id"]

    error = assert_error(client.patch(f"/api/todos/{todo_id}", json={}, headers=USER_A), 422, "VALIDATION_ERROR")

    assert "하나 이상" in error["message"]


@pytest.mark.parametrize(("method", "url"), [("POST", "/api/todos"), ("PATCH", "/api/todos/{id}")])
def test_ac_fr_010_4_unknown_field_returns_422(client: TestClient, create_todo, method: str, url: str) -> None:
    todo_id = create_todo("항목")["id"]

    response = client.request(method, url.format(id=todo_id), json={"text": "x", "done": True}, headers=USER_A)

    error = assert_error(response, 422, "VALIDATION_ERROR")
    assert {"field": "done", "message": "정의되지 않은 항목입니다."} in error["details"]


@pytest.mark.parametrize(("method", "body"), [("PATCH", {"completed": True}), ("DELETE", None)])
def test_ac_fr_010_4_invalid_uuid_path_returns_422(client: TestClient, method: str, body: Any) -> None:
    error = assert_error(client.request(method, "/api/todos/not-a-uuid", json=body, headers=USER_A), 422, "VALIDATION_ERROR")

    assert error["details"][0] == {"field": "todo_id", "message": "올바른 UUID 형식이 아닙니다."}


def test_ac_fr_010_malformed_json_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/todos", content=b'{"text": ', headers={**USER_A, "Content-Type": "application/json"}
    )

    assert_error(response, 422, "VALIDATION_ERROR")


# ───────── NFR-004 보안 ─────────


@pytest.mark.parametrize(
    ("url", "key", "vercel"),
    [("https://x.supabase.co", "", False), ("", "sb_secret_x", False), ("", "", True)],
)
def test_ac_nfr_004_1_invalid_storage_settings_fail_app_creation(url: str, key: str, vercel: bool) -> None:
    with pytest.raises(RuntimeError):
        create_app(Settings(supabase_url=url, supabase_secret_key=key, is_vercel=vercel))


class _ExplodingRepository:
    """DB 오류를 흉내 낸다. 예외 메시지에 민감 정보가 들어 있다."""

    def __getattr__(self, name: str) -> Any:
        def _raise(*_: Any, **__: Any) -> None:
            raise RuntimeError("SELECT * FROM todos -- apikey=sb_secret_leak")

        return _raise


def test_ac_nfr_004_3_internal_error_hides_details(app: FastAPI) -> None:
    app.dependency_overrides[get_todo_repository] = lambda: _ExplodingRepository()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/todos", headers=USER_A)

    error = assert_error(response, 500, "INTERNAL_ERROR")
    assert error["details"] is None
    for secret in ("sb_secret", "SELECT", "Traceback", "RuntimeError"):
        assert secret not in response.text


# ───────── NFR-005 / NFR-006 공통 ─────────


def test_ac_nfr_006_1_framework_errors_use_common_format(client: TestClient) -> None:
    assert_error(client.get("/api/unknown", headers=USER_A), 404, "NOT_FOUND")
    assert_error(client.put("/api/todos", headers=USER_A), 405, "METHOD_NOT_ALLOWED")


def test_cors_preflight_allows_frontend_origin_only(client: TestClient) -> None:
    preflight = {"Access-Control-Request-Method": "PATCH", "Access-Control-Request-Headers": "authorization,content-type"}

    allowed = client.options("/api/todos", headers={"Origin": FRONTEND_ORIGIN, **preflight})
    denied = client.options("/api/todos", headers={"Origin": "https://evil.example", **preflight})

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert "PATCH" in allowed.headers["access-control-allow-methods"]
    assert "access-control-allow-origin" not in denied.headers


def test_crud_flow_end_to_end(client: TestClient) -> None:
    """추가 → 조회 → 토글 → 수정 → 삭제를 한 흐름으로 확인한다 (CLAUDE.md 6-4 CRUD 회귀)."""
    created = client.post("/api/todos", json={"text": "흐름 테스트"}, headers=USER_A).json()
    todo_id = created["id"]

    assert [i["id"] for i in client.get("/api/todos", headers=USER_A).json()["items"]] == [todo_id]
    assert client.patch(f"/api/todos/{todo_id}", json={"completed": True}, headers=USER_A).json()["completed"] is True
    assert client.patch(f"/api/todos/{todo_id}", json={"text": "수정됨"}, headers=USER_A).json()["text"] == "수정됨"
    assert client.delete(f"/api/todos/{todo_id}", headers=USER_A).status_code == 204
    assert client.get("/api/todos", headers=USER_A).json() == {"items": []}


# ───────── FR-012 마감일 ─────────


def test_ac_fr_012_1_create_with_due_date(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": "보고서", "due_date": "2026-11-25"}, headers=USER_A)

    assert response.status_code == 201
    assert response.json()["due_date"] == "2026-11-25"
    # 목록 조회에도 같은 값이 나온다.
    assert client.get("/api/todos", headers=USER_A).json()["items"][0]["due_date"] == "2026-11-25"


@pytest.mark.parametrize("body", [{"text": "보고서"}, {"text": "보고서", "due_date": None}])
def test_ac_fr_012_1_create_without_due_date_returns_null(client: TestClient, body: dict[str, Any]) -> None:
    response = client.post("/api/todos", json=body, headers=USER_A)

    assert response.status_code == 201
    assert response.json()["due_date"] is None


def test_ac_fr_012_1_past_and_boundary_dates_are_allowed(client: TestClient) -> None:
    # 지난 날짜도 허용한다 (api-spec 2-4). 범위 양 끝도 포함한다.
    for value in ("2000-01-01", "2020-05-05", "2100-12-31", "2028-02-29"):
        response = client.post("/api/todos", json={"text": "x", "due_date": value}, headers=USER_A)
        assert response.status_code == 201, value
        assert response.json()["due_date"] == value


def test_ac_fr_012_2_patch_changes_only_due_date(client: TestClient, clock) -> None:
    created = client.post("/api/todos", json={"text": "보고서", "due_date": "2026-11-25"}, headers=USER_A).json()

    response = client.patch(f"/api/todos/{created['id']}", json={"due_date": "2026-12-01"}, headers=USER_A)

    assert response.status_code == 200
    body = response.json()
    assert body["due_date"] == "2026-12-01"
    assert body["text"] == "보고서"
    assert body["completed"] is False
    assert body["updated_at"] > created["updated_at"]


def test_ac_fr_012_2_patch_null_clears_due_date(client: TestClient) -> None:
    created = client.post("/api/todos", json={"text": "보고서", "due_date": "2026-11-25"}, headers=USER_A).json()

    response = client.patch(f"/api/todos/{created['id']}", json={"due_date": None}, headers=USER_A)

    assert response.status_code == 200
    assert response.json()["due_date"] is None
    assert client.get("/api/todos", headers=USER_A).json()["items"][0]["due_date"] is None


def test_ac_fr_012_2_patch_can_add_due_date_to_todo_without_one(client: TestClient, create_todo) -> None:
    todo_id = create_todo("마감 없음")["id"]

    response = client.patch(f"/api/todos/{todo_id}", json={"due_date": "2026-11-30"}, headers=USER_A)

    assert response.status_code == 200
    assert response.json()["due_date"] == "2026-11-30"


@pytest.mark.parametrize("body", [{"completed": True}, {"text": "바뀐 내용"}])
def test_ac_fr_012_3_patch_without_due_date_keeps_it(client: TestClient, body: dict[str, Any]) -> None:
    created = client.post("/api/todos", json={"text": "보고서", "due_date": "2026-11-25"}, headers=USER_A).json()

    response = client.patch(f"/api/todos/{created['id']}", json=body, headers=USER_A)

    assert response.status_code == 200
    assert response.json()["due_date"] == "2026-11-25"


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("2026-02-30", "존재하지 않는 날짜입니다."),
        ("2026/11/25", "마감일은 YYYY-MM-DD 형식이어야 합니다."),
        ("20261125", "마감일은 YYYY-MM-DD 형식이어야 합니다."),
        ("2026-11-25T09:00:00", "마감일은 YYYY-MM-DD 형식이어야 합니다."),
        (20261125, "마감일은 YYYY-MM-DD 형식이어야 합니다."),
        ("", "마감일은 YYYY-MM-DD 형식이어야 합니다."),
        ("２０２６-11-25", "마감일은 YYYY-MM-DD 형식이어야 합니다."),
        ("1999-12-31", "마감일은 2000-01-01부터 2100-12-31 사이여야 합니다."),
        ("2101-01-01", "마감일은 2000-01-01부터 2100-12-31 사이여야 합니다."),
    ],
)
def test_ac_fr_012_4_invalid_due_date_rejected(client: TestClient, create_todo, value: Any, message: str) -> None:
    todo_id = create_todo("항목")["id"]
    requests = (
        client.post("/api/todos", json={"text": "x", "due_date": value}, headers=USER_A),
        client.patch(f"/api/todos/{todo_id}", json={"due_date": value}, headers=USER_A),
    )

    for response in requests:
        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert error["details"][0] == {"field": "due_date", "message": message}
        assert error["message"] == message
    # 실패한 요청은 저장되지 않는다.
    items = client.get("/api/todos", headers=USER_A).json()["items"]
    assert [item["due_date"] for item in items] == [None]


def test_ac_fr_012_2_patch_due_date_follows_auth_and_ownership(client: TestClient) -> None:
    # 마감일 수정도 기존 401/403/404 규칙을 그대로 따른다 (FR-007, FR-008).
    todo_id = client.post("/api/todos", json={"text": "a", "due_date": "2026-11-25"}, headers=USER_A).json()["id"]
    body = {"due_date": None}

    assert_error(client.patch(f"/api/todos/{todo_id}", json=body), 401, "UNAUTHENTICATED")
    assert_error(client.patch(f"/api/todos/{todo_id}", json=body, headers=USER_B), 403, "FORBIDDEN")
    assert_error(client.patch(f"/api/todos/{MISSING_ID}", json=body, headers=USER_A), 404, "NOT_FOUND")
    assert client.get("/api/todos", headers=USER_A).json()["items"][0]["due_date"] == "2026-11-25"


# ───────── FR-013 카테고리 ─────────


@pytest.mark.parametrize("category", ["work", "personal", "study"])
def test_ac_fr_013_1_create_with_category(client: TestClient, category: str) -> None:
    response = client.post("/api/todos", json={"text": "보고서", "category": category}, headers=USER_A)

    assert response.status_code == 201
    assert response.json()["category"] == category
    assert client.get("/api/todos", headers=USER_A).json()["items"][0]["category"] == category


def test_ac_fr_013_1_create_without_category_defaults_to_personal(client: TestClient) -> None:
    response = client.post("/api/todos", json={"text": "보고서"}, headers=USER_A)

    assert response.status_code == 201
    assert response.json()["category"] == "personal"


def test_ac_fr_013_2_patch_changes_only_category(client: TestClient, clock) -> None:
    created = client.post(
        "/api/todos",
        json={"text": "보고서", "due_date": "2026-11-25", "category": "work"},
        headers=USER_A,
    ).json()

    response = client.patch(f"/api/todos/{created['id']}", json={"category": "study"}, headers=USER_A)

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "study"
    # 마감일 등 다른 필드는 그대로다 (기존 기능 유지)
    assert (body["text"], body["completed"], body["due_date"]) == ("보고서", False, "2026-11-25")
    assert body["updated_at"] > created["updated_at"]


@pytest.mark.parametrize(
    "body", [{"completed": True}, {"text": "바뀐 내용"}, {"due_date": None}, {"due_date": "2026-12-01"}]
)
def test_ac_fr_013_2_patch_without_category_keeps_it(client: TestClient, body: dict[str, Any]) -> None:
    created = client.post("/api/todos", json={"text": "보고서", "category": "work"}, headers=USER_A).json()

    response = client.patch(f"/api/todos/{created['id']}", json=body, headers=USER_A)

    assert response.status_code == 200
    assert response.json()["category"] == "work"


def test_ac_fr_013_2_patch_text_due_date_and_category_together(client: TestClient, create_todo) -> None:
    # 편집 모드 저장처럼 여러 필드를 한 번에 보내도 모두 반영된다.
    todo_id = create_todo("원래")["id"]

    response = client.patch(
        f"/api/todos/{todo_id}",
        json={"text": "새 내용", "due_date": "2026-12-24", "category": "study"},
        headers=USER_A,
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["text"], body["due_date"], body["category"]) == ("새 내용", "2026-12-24", "study")


@pytest.mark.parametrize("value", ["Work", "", "etc", " work", 1, ["work"], None])
def test_ac_fr_013_3_invalid_category_rejected(client: TestClient, create_todo, value: Any) -> None:
    todo_id = create_todo("항목")["id"]

    create_error = assert_error(
        client.post("/api/todos", json={"text": "x", "category": value}, headers=USER_A), 422, "VALIDATION_ERROR"
    )
    patch_error = assert_error(
        client.patch(f"/api/todos/{todo_id}", json={"category": value}, headers=USER_A), 422, "VALIDATION_ERROR"
    )

    assert create_error["details"][0]["field"] == "category"
    if value is not None:
        # PATCH의 null은 모델 수준에서 거부하므로(text·completed와 같은 규칙) field가 비어 있다.
        assert patch_error["details"][0]["field"] == "category"
        assert patch_error["message"] == "카테고리는 work, personal, study 중 하나여야 합니다."
    # 실패한 요청은 저장되지 않는다.
    items = client.get("/api/todos", headers=USER_A).json()["items"]
    assert [item["category"] for item in items] == ["personal"]


# ───────── FR-014 카테고리 필터 ─────────


def _seed(client: TestClient) -> None:
    for text, category in (("업무1", "work"), ("학습1", "study"), ("업무2", "work")):
        client.post("/api/todos", json={"text": text, "category": category}, headers=USER_A)


def test_ac_fr_014_1_filter_by_category_in_creation_order(client: TestClient) -> None:
    _seed(client)

    work = client.get("/api/todos", params={"category": "work"}, headers=USER_A)
    personal = client.get("/api/todos", params={"category": "personal"}, headers=USER_A)
    everything = client.get("/api/todos", headers=USER_A)

    assert work.status_code == 200
    assert [item["text"] for item in work.json()["items"]] == ["업무1", "업무2"]
    assert personal.json() == {"items": []}
    assert [item["text"] for item in everything.json()["items"]] == ["업무1", "학습1", "업무2"]


def test_ac_fr_014_2_filter_does_not_leak_other_users_todos(client: TestClient) -> None:
    _seed(client)
    client.post("/api/todos", json={"text": "B의 업무", "category": "work"}, headers=USER_B)

    a_items = client.get("/api/todos", params={"category": "work"}, headers=USER_A).json()["items"]
    b_items = client.get("/api/todos", params={"category": "work"}, headers=USER_B).json()["items"]

    assert [item["text"] for item in a_items] == ["업무1", "업무2"]
    assert [item["text"] for item in b_items] == ["B의 업무"]


@pytest.mark.parametrize("value", ["etc", "", "WORK"])
def test_ac_fr_014_3_invalid_filter_rejected(client: TestClient, value: str) -> None:
    error = assert_error(
        client.get("/api/todos", params={"category": value}, headers=USER_A), 422, "VALIDATION_ERROR"
    )

    assert error["details"][0] == {
        "field": "category",
        "message": "카테고리는 work, personal, study 중 하나여야 합니다.",
    }


def test_ac_fr_014_3_auth_is_checked_before_filter_validation(client: TestClient) -> None:
    assert_error(client.get("/api/todos", params={"category": "etc"}), 401, "UNAUTHENTICATED")
