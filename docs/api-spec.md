# API 명세서 (FastAPI)

| 항목 | 내용 |
| --- | --- |
| 기준 문서 | [prd.md](./prd.md) |
| 연관 문서 | [db-schema.md](./db-schema.md), [acceptance-criteria.md](./acceptance-criteria.md), [tasks.md](./tasks.md) |
| Base URL | `${VITE_API_BASE_URL}/api` (로컬 예: `http://localhost:8000/api`) |
| 데이터 포맷 | 요청/응답 모두 `application/json; charset=utf-8` |

## 1. 인증 방식

- FastAPI는 **자체 회원가입/로그인 엔드포인트를 제공하지 않는다.** (FR-007)
- 프론트엔드가 Supabase Auth 클라이언트로 로그인/로그아웃을 처리하고, 발급된 **Supabase JWT(access
  token)** 를 모든 요청의 `Authorization: Bearer <token>` 헤더에 담아 전송한다.
- FastAPI는 Supabase 프로젝트의 JWKS/서명 키로 JWT를 검증하고, 클레임의 `sub`(Supabase user id)를
  `user_id`로 사용해 요청을 처리한다. (FR-008, NFR-004)
- JWT가 없거나 유효하지 않으면 모든 `/api/todos*` 엔드포인트는 `401 Unauthorized`를 반환한다.
- **DB 접속 방식**: FastAPI는 `SUPABASE_SERVICE_ROLE_KEY`로 Supabase PostgreSQL에 연결하며, 모든
  쿼리에 JWT `sub` 클레임에서 얻은 `user_id`로 `WHERE` 절을 명시적으로 적용해 소유자 필터링을
  수행한다(FR-008). [db-schema.md](./db-schema.md) 3절의 RLS 정책은 이 서버 측 필터링이 누락되거나
  Supabase 클라이언트가 직접 접근하는 향후 경로에 대비한 이중 방어선이며, service-role 접속 자체는
  RLS를 우회하므로 RLS만으로는 FR-008을 충족하지 못한다는 점에 유의한다.

## 2. 공통 규약

### 2-1. 에러 응답 포맷

모든 에러는 아래 형태의 JSON 본문을 반환한다.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "할 일 내용을 입력해 주세요.",
    "details": null
  }
}
```

| 코드 | HTTP 상태 | 의미 | 관련 요구사항 |
| --- | --- | --- | --- |
| `UNAUTHENTICATED` | 401 | JWT 누락/만료/서명 불일치 | FR-007, NFR-004 |
| `FORBIDDEN` | 403 | 본인 소유가 아닌 리소스 접근 | FR-008 |
| `NOT_FOUND` | 404 | 대상 ToDo가 존재하지 않음(삭제됨 포함) | FR-005 |
| `VALIDATION_ERROR` | 422 | 요청 본문 검증 실패(빈 텍스트, 길이 초과 등) | FR-010 |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류(DB 연결 등) | NFR-006 |

### 2-2. 공통 응답 스키마 — `TodoResponse`

```json
{
  "id": "b3b6b1b0-7e0a-4d9a-8b0a-1a2b3c4d5e6f",
  "text": "API 명세 초안 작성",
  "completed": false,
  "created_at": "2026-11-19T07:00:00Z",
  "updated_at": "2026-11-19T07:00:00Z"
}
```

프론트엔드 [types.ts](../frontend/src/types.ts)의 `Todo { id, text, completed }`와 호환되도록
`id`, `text`, `completed` 필드명을 그대로 사용한다(스네이크/카멜 변환은 프론트 API 클라이언트 계층에서
처리). `created_at`/`updated_at`은 정렬(FR-002) 및 추후 동기화 디버깅용으로 포함한다.

## 3. 엔드포인트

### 3-1. `GET /api/todos` — 목록 조회

- **관련 요구사항**: FR-002, FR-008, NFR-007
- **인증**: 필수
- **쿼리 파라미터**: 없음 (정렬은 항상 `created_at ASC` 고정, 페이지네이션은 Out-of-scope)
- **응답 200**:

```json
{
  "items": [ { "id": "...", "text": "...", "completed": false, "created_at": "...", "updated_at": "..." } ]
}
```

- **에러**: `UNAUTHENTICATED`(401)
- **수용 기준**: 로그인한 사용자 본인 소유 ToDo만 반환되어야 한다 (타 사용자 데이터 미포함, FR-008).

### 3-2. `POST /api/todos` — 생성

- **관련 요구사항**: FR-001, FR-010
- **인증**: 필수
- **요청 본문** — `TodoCreateRequest`:

```json
{ "text": "API 명세 초안 작성" }
```

| 필드 | 타입 | 제약 | 관련 요구사항 |
| --- | --- | --- | --- |
| `text` | string | 서버에서 `trim()` 후 1~500자. 공백만 있으면 `VALIDATION_ERROR` | FR-001, FR-010 |

- **응답 201**: `TodoResponse` (신규 생성된 ToDo, `completed: false` 고정)
- **에러**: `UNAUTHENTICATED`(401), `VALIDATION_ERROR`(422)

### 3-3. `PATCH /api/todos/{todo_id}` — 수정(텍스트/완료 상태)

- **관련 요구사항**: FR-003, FR-004, FR-008, FR-010
- **인증**: 필수
- **경로 파라미터**: `todo_id` (UUID)
- **요청 본문** — `TodoUpdateRequest` (부분 업데이트, 둘 중 최소 1개 필드 필요):

```json
{ "text": "수정된 내용", "completed": true }
```

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `text` | string (optional) | 제공 시 `trim()` 후 1~500자 검증 (FR-004, FR-010) |
| `completed` | boolean (optional) | 제공 시 그대로 반영 (FR-003) |

- **응답 200**: 갱신된 `TodoResponse`
- **에러**: `UNAUTHENTICATED`(401), `VALIDATION_ERROR`(422, 빈 텍스트/양 필드 모두 누락),
  `NOT_FOUND`(404, 존재하지 않는 id), `FORBIDDEN`(403, 타인 소유 — RLS와 이중 방어)
- **비고**: 체크박스 토글(FR-003)과 텍스트 저장(FR-004)을 하나의 엔드포인트로 통합해 프론트의
  `toggleTodo`/`updateTodo` 두 호출을 동일 API로 매핑한다.

### 3-4. `DELETE /api/todos/{todo_id}` — 삭제

- **관련 요구사항**: FR-005, FR-008
- **인증**: 필수
- **응답 204**: 본문 없음
- **에러**: `UNAUTHENTICATED`(401), `NOT_FOUND`(404), `FORBIDDEN`(403)

## 4. 요구사항 ↔ 엔드포인트 매핑표

| 요구사항 ID | 엔드포인트 |
| --- | --- |
| FR-001 | `POST /api/todos` |
| FR-002 | `GET /api/todos` |
| FR-003 | `PATCH /api/todos/{id}` (`completed` 필드) |
| FR-004 | `PATCH /api/todos/{id}` (`text` 필드) |
| FR-005 | `DELETE /api/todos/{id}` |
| FR-006 | 클라이언트가 `GET /api/todos` 응답으로 `ProgressMeter` 계산(별도 API 없음) |
| FR-007 | 모든 엔드포인트의 `Authorization` 헤더 검증 |
| FR-008 | 모든 엔드포인트의 소유자 필터링(`WHERE user_id = :jwt_sub`) + `FORBIDDEN`/`NOT_FOUND` 처리 |
| FR-009 | 모든 쓰기 엔드포인트가 Supabase PostgreSQL에 커밋 후 응답 |
| FR-010 | `POST /api/todos`, `PATCH /api/todos/{id}` 요청 검증 |

## 5. 명시적으로 제공하지 않는 것

- ToDo 단건 조회(`GET /api/todos/{id}`)는 현재 UI가 목록 전체만 사용하므로 범위에서 제외한다
  (필요 시 TASKS에서 백로그로 기록).
- 페이지네이션/검색/정렬 파라미터는 Out-of-scope(PRD 4-2).
