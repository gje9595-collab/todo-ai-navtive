# DB 스키마 (Supabase / PostgreSQL)

| 항목 | 내용 |
| --- | --- |
| 기준 문서 | [prd.md](./prd.md), [api-spec.md](./api-spec.md) |
| 연관 문서 | [acceptance-criteria.md](./acceptance-criteria.md), [tasks.md](./tasks.md) |
| 저장 위치(예정) | `supabase/migrations/0001_create_todos.sql` |

## 1. ERD 개요

```
auth.users (Supabase 기본 제공)
    │ 1
    │
    │ N
public.todos
```

`auth.users`는 Supabase Auth가 관리하는 테이블로 이번 범위에서 직접 수정하지 않는다(FR-007 Out-of-scope).
앱이 소유하는 테이블은 `public.todos` 하나뿐이다.

## 2. `public.todos` 테이블

| 컬럼 | 타입 | 제약 | 관련 요구사항 |
| --- | --- | --- | --- |
| `id` | `uuid` | PK, `default gen_random_uuid()` | FR-001, FR-009 |
| `user_id` | `uuid` | NOT NULL, FK → `auth.users(id)` ON DELETE CASCADE | FR-007, FR-008 |
| `text` | `varchar(500)` | NOT NULL, `check (length(btrim(text)) > 0)` | FR-010 |
| `completed` | `boolean` | NOT NULL, `default false` | FR-003 |
| `created_at` | `timestamptz` | NOT NULL, `default now()` | FR-002, FR-009 |
| `updated_at` | `timestamptz` | NOT NULL, `default now()` | FR-004, FR-009 |

### 2-1. 마이그레이션 SQL (초안)

```sql
-- supabase/migrations/0001_create_todos.sql
create table if not exists public.todos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  text varchar(500) not null,
  completed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint todos_text_not_blank check (length(btrim(text)) > 0)
);

create index if not exists todos_user_id_created_at_idx
  on public.todos (user_id, created_at asc);

-- updated_at 자동 갱신 트리거
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at := now();
  return new;
end;
$$ language plpgsql;

create trigger todos_set_updated_at
  before update on public.todos
  for each row
  execute function public.set_updated_at();
```

- **인덱스**: `(user_id, created_at)` 복합 인덱스로 FR-002의 "본인 소유 목록을 생성일 순 조회" 쿼리를
  지원한다(NFR-007).
- **체크 제약**: `todos_text_not_blank`는 서버 검증(FR-010)의 최종 방어선으로, API 계층 우회 시에도
  빈 텍스트 저장을 막는다.
- **CASCADE 삭제**: Supabase Auth에서 사용자가 삭제되면 해당 사용자의 ToDo도 함께 삭제되어 고아 행을
  남기지 않는다.

## 3. RLS(Row Level Security) 정책

Supabase 테이블은 기본적으로 `anon`/`authenticated` 역할이 PostgREST/클라이언트로 직접 접근 가능하므로,
FastAPI가 service-role로 우회하더라도 **RLS를 반드시 활성화**해 이중 방어를 구성한다(NFR-004, FR-008).

```sql
alter table public.todos enable row level security;

create policy "todos_select_own" on public.todos
  for select using (auth.uid() = user_id);

create policy "todos_insert_own" on public.todos
  for insert with check (auth.uid() = user_id);

create policy "todos_update_own" on public.todos
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "todos_delete_own" on public.todos
  for delete using (auth.uid() = user_id);
```

| 정책 | 대응 API | 관련 요구사항 |
| --- | --- | --- |
| `todos_select_own` | `GET /api/todos` | FR-002, FR-008 |
| `todos_insert_own` | `POST /api/todos` | FR-001, FR-008 |
| `todos_update_own` | `PATCH /api/todos/{id}` | FR-003, FR-004, FR-008 |
| `todos_delete_own` | `DELETE /api/todos/{id}` | FR-005, FR-008 |

> FastAPI가 `service_role` 키로 접근할 경우 RLS가 우회되므로, 백엔드 코드 레벨에서도 모든 쿼리에
> `WHERE user_id = :jwt_sub`를 명시해야 한다(코드 리뷰 체크 항목, TASKS 참조). RLS는 Supabase
> 클라이언트(anon/authenticated 키)를 직접 사용하는 향후 경로에 대한 안전망이다.

## 4. 요구사항 ↔ 스키마 매핑표

| 요구사항 ID | 스키마 요소 |
| --- | --- |
| FR-001 | `todos` 테이블 INSERT, `todos_insert_own` 정책 |
| FR-002 | `(user_id, created_at)` 인덱스, `todos_select_own` 정책 |
| FR-003 | `completed` 컬럼 UPDATE |
| FR-004 | `text` 컬럼 UPDATE, `updated_at` 트리거 |
| FR-005 | `todos_delete_own` 정책 |
| FR-007, FR-008 | `user_id` FK + 모든 RLS 정책 |
| FR-009 | 테이블 자체(영속 저장소) |
| FR-010 | `varchar(500)` + `todos_text_not_blank` check 제약 |

## 5. 비고 및 향후 확장 여지(Out-of-scope 기록)

- 사용자 지정 정렬(드래그 순서) 필요 시 `position integer` 컬럼 추가 검토 — 이번 범위 아님(PRD 9절).
- 소프트 삭제(휴지통) 요구 발생 시 `deleted_at timestamptz` 컬럼 추가 검토 — 이번 범위 아님.
