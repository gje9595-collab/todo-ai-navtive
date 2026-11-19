# 수용 기준 (Acceptance Criteria)

| 항목 | 내용 |
| --- | --- |
| 기준 문서 | [prd.md](./prd.md), [api-spec.md](./api-spec.md), [db-schema.md](./db-schema.md) |
| 형식 | Given–When–Then |
| 연관 문서 | [tasks.md](./tasks.md) |

각 기준은 PRD의 요구사항 ID를 그대로 사용한다. 괄호 안은 검증 대상 구현 위치를 가리킨다.

## FR-001 — ToDo 생성

- **AC-FR-001-1**: Given 로그인한 사용자가 입력창에 공백이 아닌 텍스트를 입력했을 때, When "추가" 버튼을
  누르거나 Enter를 치면, Then `POST /api/todos` 호출 후 목록 맨 끝에 새 항목이 `completed: false`로
  표시된다. (`TodoInput.tsx`, API 3-2)
- **AC-FR-001-2**: Given 입력창이 비어 있거나 공백만 있을 때, When 추가를 시도하면, Then 요청이 전송되지
  않고 "추가" 버튼은 비활성(`disabled`) 상태를 유지한다. (`TodoInput.tsx`)
- **AC-FR-001-3**: Given 추가에 성공했을 때, When 응답을 받으면, Then 입력창은 비워지고 포커스는 입력창에
  유지된다.

## FR-002 — 목록 조회

- **AC-FR-002-1**: Given 로그인한 사용자 A가 ToDo 3건을 생성했을 때, When 다른 기기에서 같은 계정으로
  로그인해 목록을 조회하면, Then 동일한 3건이 생성 순서(오름차순)대로 표시된다. (API 3-1, DB 2절 인덱스)
- **AC-FR-002-2**: Given ToDo가 하나도 없을 때, When 목록을 조회하면, Then 빈 배열을 응답받고 프론트는
  "첫 할 일을 위에 입력해 보세요." 안내 문구를 표시한다. (`App.tsx` empty state)

## FR-003 — 완료 토글

- **AC-FR-003-1**: Given 미완료 ToDo가 있을 때, When 체크박스를 클릭하면, Then
  `PATCH /api/todos/{id}` `{completed: true}` 요청이 전송되고 체크박스가 체크되며 텍스트에 취소선이
  적용된다. (`TodoItem.tsx .is-done`)
- **AC-FR-003-2**: Given 완료 ToDo가 있을 때, When 체크박스를 다시 클릭하면, Then `completed: false`로
  되돌아간다.

## FR-004 — 텍스트 수정

- **AC-FR-004-1**: Given 목록에 ToDo가 있을 때, When "수정" 버튼을 누르면, Then 인라인 편집 입력창이
  나타나고 기존 텍스트가 채워진 채 자동 포커스된다. (`TodoItem.tsx startEdit`)
- **AC-FR-004-2**: Given 편집 모드에서 텍스트를 변경했을 때, When "저장"을 누르면, Then
  `PATCH /api/todos/{id}` `{text}` 요청이 전송되고 성공 시 편집 모드가 종료되며 포커스가 "수정" 버튼으로
  복귀한다. (NFR-003)
- **AC-FR-004-3**: Given 편집 모드에서 입력을 모두 지웠을 때, When "저장"을 누르면, Then 요청이 전송되지
  않고 "저장" 버튼은 비활성 상태를 유지한다.
- **AC-FR-004-4**: Given 편집 모드일 때, When Esc 키를 누르면, Then 변경 사항이 버려지고 원래 텍스트로
  복귀하며 포커스가 "수정" 버튼으로 돌아간다. (`cancelEdit`)

## FR-005 — 삭제

- **AC-FR-005-1**: Given 목록에 ToDo가 있을 때, When "삭제" 버튼을 누르면, Then
  `DELETE /api/todos/{id}` 요청이 전송되고 성공 시 해당 항목이 목록에서 사라지며 포커스는 새 ToDo
  입력창으로 이동한다. (NFR-003, `deleteTodo`)
- **AC-FR-005-2**: Given 이미 삭제된 ToDo에 대해 지연 응답으로 재요청이 발생했을 때, When
  서버가 `404 NOT_FOUND`를 반환하면, Then 프론트는 해당 항목을 목록에서 제거된 상태로 유지하고 에러를
  사용자에게 노출하지 않는다(멱등 처리). (NFR-006)

## FR-006 — 완료율 표시

- **AC-FR-006-1**: Given ToDo가 24개 이하일 때, When 목록이 변경되면, Then `ProgressMeter`는 항목별
  세그먼트 바를 표시하고 완료된 항목만 `is-done` 색상으로 칠해진다.
- **AC-FR-006-2**: Given ToDo가 24개를 초과할 때, When 목록이 변경되면, Then 세그먼트 대신 연속형 진행률
  막대(`meter-fill`, width %)로 전환된다.
- **AC-FR-006-3**: Given 완료율이 변경될 때, When DOM이 갱신되면, Then `aria-live="polite"` 영역의
  텍스트(`n개 중 m개 완료`)가 스크린 리더에 공지된다. (NFR-001)

## FR-007 — 인증

- **AC-FR-007-1**: Given 로그인하지 않은 사용자가, When `GET/POST/PATCH/DELETE /api/todos*`를 직접
  호출하면, Then `401 UNAUTHENTICATED` 에러가 반환된다.
- **AC-FR-007-2**: Given 유효한 Supabase 세션이 만료되었을 때, When ToDo API를 호출하면, Then 401 응답을
  받고 프론트는 사용자에게 재로그인을 안내한다(구체 UX는 Out-of-scope, 에러 처리만 검증). (NFR-006)

## FR-008 — 사용자별 데이터 격리

- **AC-FR-008-1**: Given 사용자 A와 B가 각각 ToDo를 가지고 있을 때, When 사용자 A가 목록을 조회하면,
  Then 사용자 B의 ToDo는 응답에 포함되지 않는다.
- **AC-FR-008-2**: Given 사용자 A가 사용자 B 소유 ToDo의 id를 알고 있을 때, When A가 해당 id로
  `PATCH`/`DELETE`를 호출하면, Then `403 FORBIDDEN` 또는 `404 NOT_FOUND`가 반환되고 B의 데이터는
  변경되지 않는다. (DB RLS 정책 + API 소유자 검사 이중 검증)

## FR-009 — 영속성

- **AC-FR-009-1**: Given 로그인한 사용자가 ToDo를 생성/수정/삭제/토글했을 때, When 브라우저를
  새로고침하면, Then 변경된 최종 상태가 그대로 유지된다(React state 초기화와 무관).
- **AC-FR-009-2**: Given 동일 계정으로 다른 브라우저 세션에서 접속했을 때, When 목록을 조회하면, Then
  최신 상태가 동일하게 반영된다.

## FR-010 — 서버 측 입력 검증

- **AC-FR-010-1**: Given `text`가 공백만으로 구성된 생성/수정 요청이, When 서버에 도달하면, Then
  `422 VALIDATION_ERROR`가 반환되고 DB에 반영되지 않는다(프론트 검증 우회 시나리오 포함, 예: API 직접
  호출).
- **AC-FR-010-2**: Given `text` 길이가 500자를 초과하는 요청이, When 서버에 도달하면, Then
  `422 VALIDATION_ERROR`가 반환된다.

## NFR-001 — 접근성

- **AC-NFR-001-1**: Given 스크린 리더 사용자가 목록을 탐색할 때, When 체크박스에 포커스하면, Then 연결된
  `<label>`의 텍스트가 읽힌다(네이티브 `<input type="checkbox">` + `appearance: none` 유지).
- **AC-NFR-001-2**: Given 키보드만 사용하는 사용자가, When Tab으로 "수정"/"삭제" 버튼에 포커스하면, Then
  각 버튼의 `aria-label`이 할 일 내용을 포함해 모호하지 않게 안내된다.

## NFR-002 — 반응형

- **AC-NFR-002-1**: Given 뷰포트 폭이 360px 이상일 때, When 카드가 렌더링되면, Then 수정/삭제 버튼이
  텍스트와 한 줄에 표시된다.
- **AC-NFR-002-2**: Given 뷰포트 폭이 359px 이하일 때, When 카드가 렌더링되면, Then 수정/삭제 버튼이 다음
  줄로 줄바꿈된다(`@media (max-width: 359px)`).

## NFR-003 — 포커스 관리

- (AC-FR-004-2, AC-FR-004-4, AC-FR-005-1에 통합 기술됨 — 중복 작성하지 않음)

## NFR-004 — 보안

- **AC-NFR-004-1**: Given 저장소 전체를 검색할 때, When `SUPABASE_SERVICE_ROLE_KEY` 문자열을 찾으면,
  Then 프론트엔드 번들/커밋된 소스에 해당 값이 하드코딩되어 있지 않아야 한다(환경변수로만 주입).
- **AC-NFR-004-2**: Given `Authorization` 헤더가 없는 요청이, When 어떤 `/api/todos*` 엔드포인트든
  호출하면, Then 비즈니스 로직 실행 전에 401로 차단된다(미들웨어/의존성 주입 단계에서 처리 확인).

## NFR-005 — 배포

- **AC-NFR-005-1**: Given Vercel 프로젝트 설정이 완료된 상태에서, When 프론트엔드를 배포하면, Then
  `VITE_API_BASE_URL` 환경변수를 통해 배포된 FastAPI 엔드포인트와 통신한다.

## NFR-006 — 에러 처리

- **AC-NFR-006-1**: Given 네트워크 오류로 `POST /api/todos`가 실패했을 때, When 프론트가 낙관적으로
  목록에 항목을 먼저 추가했다면, Then 실패 확인 즉시 해당 항목을 롤백하고 사용자에게 실패를 알린다.

## NFR-007 — 성능

- **AC-NFR-007-1**: Given ToDo 200건을 가진 계정으로, When `GET /api/todos`를 호출하면, Then p95
  응답 시간이 500ms 이하다(측정은 TASKS의 부하 테스트 작업에서 수행).
