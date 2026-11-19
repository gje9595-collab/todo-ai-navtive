# 구현 TASKS

| 항목 | 내용 |
| --- | --- |
| 기준 문서 | [prd.md](./prd.md), [api-spec.md](./api-spec.md), [db-schema.md](./db-schema.md), [acceptance-criteria.md](./acceptance-criteria.md) |
| 표기 | `관련 요구사항`은 PRD의 FR/NFR ID를 인용. `선행 작업`은 이 문서 내 Task ID를 참조 |

작업은 레이어(DB → Backend → Frontend 연동 → 품질/배포) 순서로 묶었으며, 같은 레이어 내에서는 병렬
진행이 가능하다.

## 1. DB / Supabase

| Task ID | 작업 | 관련 요구사항 | 선행 작업 |
| --- | --- | --- | --- |
| T-01 | Supabase 프로젝트 생성 및 `supabase/migrations/` 디렉터리 초기화 | FR-009 | - |
| T-02 | `0001_create_todos.sql` 마이그레이션 작성 ([db-schema.md](./db-schema.md) 2-1절 SQL 적용) | FR-001, FR-003, FR-004, FR-005, FR-009, FR-010 | T-01 |
| T-03 | `(user_id, created_at)` 인덱스 및 `updated_at` 트리거 적용 확인 | FR-002, FR-004 | T-02 |
| T-04 | RLS 활성화 및 4개 정책(select/insert/update/delete own) 적용 | FR-007, FR-008, NFR-004 | T-02 |
| T-05 | RLS 정책 검증: 2개 테스트 계정으로 교차 접근 시도 후 차단 확인 (AC-FR-008-1/2) | FR-008 | T-04 |

## 2. Backend (FastAPI)

| Task ID | 작업 | 관련 요구사항 | 선행 작업 |
| --- | --- | --- | --- |
| T-10 | `backend/` 디렉터리 스캐폴딩 (`app/main.py`, `routers/`, `schemas/`, `services/`, `core/`, `requirements.txt`) | README 목표 구조 | - |
| T-11 | Supabase JWT 검증 의존성(`core/auth.py`) 구현: JWKS 조회, `sub` 추출, 실패 시 401 | FR-007, NFR-004 | T-10 |
| T-12 | Pydantic 스키마 정의: `TodoCreateRequest`, `TodoUpdateRequest`, `TodoResponse`, 에러 응답 모델 | API 명세 2절 | T-10 |
| T-13 | `GET /api/todos` 구현 (소유자 필터 + 생성일 정렬) | FR-002, FR-008, NFR-007 | T-02, T-11, T-12 |
| T-14 | `POST /api/todos` 구현 (trim/길이 검증 포함) | FR-001, FR-008, FR-010 | T-02, T-11, T-12 |
| T-15 | `PATCH /api/todos/{todo_id}` 구현 (text/completed 부분 업데이트, 소유자 아니면 403/404) | FR-003, FR-004, FR-008, FR-010 | T-02, T-11, T-12 |
| T-16 | `DELETE /api/todos/{todo_id}` 구현 (소유자 아니면 403/404, 멱등성 고려) | FR-005, FR-008 | T-02, T-11, T-12 |
| T-17 | 공통 예외 핸들러로 에러 응답 포맷 통일(`{error:{code,message,details}}`) | API 명세 2-1절, NFR-006 | T-12 |
| T-18 | 백엔드 단위/통합 테스트 작성 (각 엔드포인트의 정상/검증 실패/인가 실패 케이스) | FR-001~FR-010 전체 | T-13~T-17 |

## 3. Frontend API 연동

| Task ID | 작업 | 관련 요구사항 | 선행 작업 |
| --- | --- | --- | --- |
| T-20 | `src/api/todosApi.ts` 작성: fetch 래퍼로 4개 엔드포인트 호출, JWT 첨부 | API 명세 3절 | T-13~T-16 |
| T-21 | `src/lib/supabaseClient.ts` 작성: Supabase Auth 클라이언트 초기화, 세션 토큰 획득 | FR-007 | T-20 |
| T-22 | `App.tsx`의 로컬 `useState` 기반 CRUD 함수를 `todosApi` 호출로 교체, 마운트 시 `GET /api/todos` 로딩 | FR-001~FR-006, FR-009 | T-20, T-21 |
| T-23 | 낙관적 업데이트 + 실패 시 롤백 로직 추가 (추가/토글/수정/삭제 공통 패턴) | NFR-006 | T-22 |
| T-24 | 로딩/에러 상태 UI 추가(목록 로딩 스피너, 에러 배너) — 기존 empty state와 공존 | NFR-006 | T-22 |
| T-25 | 미로그인 상태 가드 (로그인 필요 안내, API 미호출) — 로그인 화면 자체는 Out-of-scope | FR-007 | T-21 |
| T-26 | 기존 접근성/포커스 관리(`returnFocus`, `inputRef`) 로직이 비동기 API 응답 이후에도 동일하게 동작하도록 회귀 검증 | NFR-001, NFR-003 | T-22 |
| T-27 | `demoTodos.ts`(`?demo` 샘플 데이터)가 API 연동 이후에도 개발 환경 전용으로만 동작하도록 유지(프로덕션 분기 유지) | 개발 편의, Out-of-scope 아님(기존 기능 유지) | T-22 |

## 4. 품질 / 접근성 / 반응형 회귀 검증

| Task ID | 작업 | 관련 요구사항 | 선행 작업 |
| --- | --- | --- | --- |
| T-30 | [acceptance-criteria.md](./acceptance-criteria.md)의 모든 AC 항목을 체크리스트로 수동/자동 검증 | FR-001~FR-010, NFR-001~007 | T-22~T-26 |
| T-31 | 스크린 리더(NVDA/VoiceOver) 또는 접근성 트리 점검으로 `aria-label`/`aria-live`/label 연결 재확인 | NFR-001 | T-30 |
| T-32 | 360px/359px 경계 반응형 수동 확인(`docs/ui-guidelines.md` 갱신 여부 검토) | NFR-002 | T-30 |
| T-33 | `npm run build`(`tsc -b` 타입 검사 포함) 및 `npm run lint`(`oxlint`) 통과 확인 | 품질 게이트 | T-22 |
| T-34 | 200건 규모 더미 데이터로 `GET /api/todos` p95 응답시간 측정 | NFR-007 | T-13 |

## 5. 배포

| Task ID | 작업 | 관련 요구사항 | 선행 작업 |
| --- | --- | --- | --- |
| T-40 | Vercel 프로젝트 2개(프론트/백엔드) 또는 모노레포 구성, 환경변수(`VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) 등록 | NFR-005, README 환경변수 표 | T-18, T-33 |
| T-41 | `SUPABASE_SERVICE_ROLE_KEY`가 백엔드 전용 환경에만 설정되고 프론트 번들에 포함되지 않는지 빌드 산출물 점검 | NFR-004 | T-40 |
| T-42 | 배포 후 스모크 테스트: 로그인 → 생성 → 새로고침 → 데이터 유지 확인 (AC-FR-009-1) | FR-009, NFR-005 | T-40 |

## 6. 우선순위 및 진행 순서 권장

1. **1단계(기반)**: T-01~T-05 (DB) → T-10~T-18 (Backend) 병행 가능하되 T-02 완료 후 백엔드 CRUD 착수.
2. **2단계(연동)**: T-20~T-27 (Frontend 연동)은 Backend 엔드포인트가 하나씩 완성되는 대로 순차 연동 가능.
3. **3단계(검증)**: T-30~T-34는 2단계 산출물이 모일수록 점진적으로 수행, 최종 회귀는 전체 완료 후 1회 더.
4. **4단계(배포)**: T-40~T-42는 1~3단계가 안정화된 뒤 진행.

## 7. 의존성 그래프 참고(세션 작업 트래커)

본 TASKS는 세션 SQL의 `todos`/`todo_deps` 테이블에도 동일한 ID 체계로 등록해 진행 상태를 추적한다
(문서와 트래커 간 ID 불일치가 없도록 Task ID를 그대로 사용).
