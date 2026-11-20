
# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소의 코드를 분석, 수정, 개발할 때 따라야 할 프로젝트 지침을 정의합니다.

## 1. 언어 정책 (Language Policy)

### 1-1. 기본 언어

- 모든 사용자 응답은 한국어로 작성한다.
- 사용자가 별도로 요청하지 않는 한 한국어를 기본 언어로 사용한다.
- 기술적인 설명, 분석 결과, 작업 계획 및 진행 상황은 한국어로 작성한다.
- 전문 용어는 필요한 경우 영어를 병기한다.
  - 예: 컨텍스트 엔지니어링(Context Engineering)
  - 예: 상태 관리(State Management)
- 제목, 표, 요약 및 결과 보고서도 한국어로 작성한다.

### 1-2. 작업 과정 및 결과 설명

- 작업 계획(Plan)은 한국어로 작성한다.
- 작업 진행 상황과 수행 결과를 한국어로 설명한다.
- 코드 수정 이유와 변경 사항을 한국어로 설명한다.
- 오류 발생 시 원인과 해결 방법을 한국어로 설명한다.
- 테스트 결과와 검증 내용을 한국어로 설명한다.
- 작업 완료 시 변경 파일, 주요 변경 내용 및 검증 결과를 한국어로 요약한다.

### 1-3. 코드 및 문서 작성 규칙

- 변수명, 함수명, 클래스명 및 파일명은 영어를 사용한다.
- 코드 주석과 Docstring은 한국어로 작성한다.
- README.md 및 프로젝트 문서는 한국어로 작성한다.
- Git 커밋 메시지는 한국어로 작성한다.
- API 경로, 라이브러리 이름, 환경 변수 및 명령어는 원문을 유지한다.
- 외부 라이브러리의 API 명칭과 코드 문법은 임의로 번역하지 않는다.

### 1-4. Agent 및 도구 실행

- Subagent의 작업 결과를 사용자에게 한국어로 설명한다.
- Skill 실행 결과를 한국어로 요약한다.
- MCP 도구 실행 결과를 한국어로 해설한다.
- Hook 실행 결과 중 사용자에게 필요한 내용을 한국어로 설명한다.
- OMC를 통한 작업 계획, 진행 상황 및 최종 결과를 한국어로 설명한다.
- 외부 도구의 원본 로그와 시스템 오류 메시지는 변경하지 않는다.
- 영어로 출력된 도구 결과는 필요한 경우 한국어로 해석하여 설명한다.

### 1-5. 출력 형식

- 모든 설명은 한국어를 기본으로 한다.
- 복잡한 작업은 단계별로 설명한다.
- 기술 비교 및 분석은 가능한 경우 표로 정리한다.
- 코드 블록 내부의 명령어와 문법은 원문을 유지한다.
- 사용자에게 제공하는 최종 요약은 한국어로 작성한다.

### 1-6. 언어 정책 적용 원칙

- 사용자에게 보여주는 설명은 한국어를 우선한다.
- 사용자가 영어 출력을 명시적으로 요청하면 해당 요청을 따른다.
- 시스템 및 상위 우선순위 지침과 충돌하는 경우 상위 지침을 따른다.
- CLI 자체 메뉴, 외부 도구의 원본 출력 등 제어할 수 없는 영역에는 적용을 보장하지 않는다.

---

## 2. 프로젝트 개요 (Project)

이 프로젝트는 React(Vite, TypeScript), FastAPI, Supabase를 기반으로 개발하고 Vercel에 배포할 예정인 ToDo List 애플리케이션입니다.

목표 디렉터리 구조와 환경 변수 구성은 `README.md`를 참고합니다.

### 2-1. 현재 개발 상태

| 영역 | 상태 |
| --- | --- |
| `frontend/` | `src/api/`를 통해 FastAPI와 연동됨 |
| `backend/` | FastAPI REST API 구현됨. 저장소는 **In-Memory**(서버 재시작 시 데이터 소멸) |
| `supabase/` | 미구현 (DB, RLS, Supabase Auth 모두 예정) |

인증은 개발용 `dev` 모드만 있습니다. `Authorization: Bearer <token>`의 토큰 값을 서명 검증 없이 그대로 `user_id`로 사용합니다.

요구사항과 설계는 `docs/`에 있으며, 코드 주석은 그 ID(`FR-xxx`, `NFR-xxx`, `AC-...`, `API 명세 n절`)를 인용합니다.

| 문서 | 내용 |
| --- | --- |
| `docs/prd.md` | 요구사항(FR/NFR) |
| `docs/api-spec.md` | 엔드포인트, 공통 에러 포맷 |
| `docs/db-schema.md` | 예정된 Supabase 스키마, RLS |
| `docs/acceptance-criteria.md` | 인수 기준(테스트 이름이 이 ID를 따름) |
| `docs/tasks.md` | 구현 Task 목록(T-xx) |

---

## 3. 실행 명령어 (Commands)

### 3-1. Frontend (`frontend/`에서 실행)

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc -b 타입 검사 + vite build
npm run lint     # ESLint가 아닌 oxlint (.oxlintrc.json)
```

프론트엔드 테스트 러너는 없습니다. 타입 검사는 `npm run build`로 수행합니다.

환경 변수는 `frontend/.env.example` 참고:

- `VITE_API_BASE_URL` (기본 `http://localhost:8000`, `/api`는 붙이지 않음)
- `VITE_DEV_AUTH_TOKEN` (기본 `dev-user`)

### 3-2. Backend (`backend/`에서 실행)

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload                      # http://localhost:8000, 문서: /docs
pytest                                             # 전체 테스트
pytest tests/test_todos_api.py::test_health        # 단일 테스트
pytest -k ac_fr_008                                # 인수 기준 ID로 선택
```

환경 변수: `CORS_ORIGINS`(쉼표 구분, 기본 `http://localhost:5173`), `AUTH_MODE`(현재 `dev`만 허용, 그 외 값이면 앱 생성 시 `RuntimeError`).

화면 검증 시에는 백엔드를 먼저 띄워야 합니다. 백엔드가 없으면 프론트는 "서버에 연결할 수 없습니다" 오류 상태로 표시됩니다.

---

## 4. 아키텍처 (Architecture)

### 4-0. Backend 계층 구조

요청은 `routers → services → repositories` 순서로 흐르며 계층마다 책임이 분리되어 있습니다.

- `routers/todos.py`: HTTP 입출력 변환만 담당. `schemas/`의 Pydantic 모델(`TodoResponse.from_model`)로 변환
- `services/todo_service.py`: 비즈니스 규칙. 소유권 검사(없으면 404, 타인 소유면 403), `updated_at` 갱신. 테스트용 `clock` 주입 가능
- `repositories/todo_repository.py`: `TodoRepository` Protocol + `InMemoryTodoRepository`. Supabase 연동 시 같은 인터페이스의 구현체로 교체
- `models/todo.py`: 불변 dataclass. 수정은 `dataclasses.replace`로 수행
- `core/auth.py`: `CurrentUserId` 의존성. Supabase JWT 검증으로 바꿀 때 이 파일만 교체하도록 설계됨
- `core/errors.py`: `AppError` 하위 클래스를 raise하면 모든 에러가 `{"error": {code, message, details}}` 형태로 응답됨. 검증 오류는 `422 VALIDATION_ERROR`
- `main.py`: `create_app(settings)` 팩토리. 저장소는 `app.state.todo_repository`에 앱마다 하나씩 생성되며 `dependencies.py`에서 주입

텍스트 검증(trim 후 1~500자)과 `StrictStr`/`StrictBool` 사용은 `schemas/todo.py`에 있습니다. PATCH는 `text`, `completed` 중 최소 하나가 필요합니다.

테스트(`tests/conftest.py`)는 테스트마다 `create_app()`으로 새 앱을 만들어 저장소를 격리합니다. `USER_A`/`USER_B` 헤더와 공통 에러 포맷 검사 헬퍼 `assert_error`를 재사용합니다.

### 4-1. Frontend 상태 관리와 API 연동

`App.tsx`가 단일 `todos: Todo[]` 상태와 `loadState`(`loading | ready | error`)를 관리하고, 하위 컴포넌트는 Props로 이벤트 핸들러를 받습니다.

- `src/api/client.ts`: `apiRequest`가 Base URL, Bearer 토큰, 공통 에러 포맷을 `ApiError(status, code, message)`로 변환. 네트워크 실패는 `NETWORK_ERROR`
- `src/api/todos.ts`: 서버 DTO(snake_case)를 프론트 `Todo`(`id`, `text`, `completed`)로 변환

CRUD별 업데이트 전략이 다르므로 수정 시 유지해야 합니다.

| 동작 | 전략 |
| --- | --- |
| 추가 | 서버가 id를 발급하므로 응답을 받은 뒤 목록에 추가 |
| 토글/수정 | 낙관적 업데이트(Optimistic Update), 실패 시 바뀐 필드만 롤백 |
| 삭제 | 먼저 제거 + 입력창 포커스, `NOT_FOUND`는 성공으로 간주, 그 외 실패는 원래 위치에 복구 |

목록 조회 `useEffect`는 `ignore` 플래그로 StrictMode 이중 실행 및 늦게 도착한 응답을 무시합니다. 오류는 `role="alert"` 알림(`notice`)으로 표시합니다.

### 4-2. TodoItem 컴포넌트

`TodoItem`은 편집 기능에 필요한 로컬 상태만 관리합니다.

```typescript
isEditing
draft
```

- `isEditing`: 현재 편집 모드 여부
- `draft`: 편집 중인 임시 입력값

### 4-3. ProgressMeter 컴포넌트

`ProgressMeter`는 `todos` 상태를 기반으로 완료율을 계산합니다.

- 작업이 24개 이하인 경우 작업별 세그먼트를 표시합니다.
- 작업이 24개를 초과하면 연속형 진행률 막대로 전환합니다.

완료율은 별도의 상태로 중복 저장하지 않고 기존 ToDo 데이터에서 계산합니다.

### 4-4. UI 스타일링

현재 별도의 UI 라이브러리는 사용하지 않습니다.

스타일은 일반 CSS로 작성하며 다음 파일에서 관리합니다.

```text
src/index.css
```

디자인 시스템은 `:root`에 정의된 CSS 사용자 정의 속성(Custom Properties)을 사용합니다.

다크 모드는 다음 미디어 쿼리를 통해 처리합니다.

```css
@media (prefers-color-scheme: dark) {
  /* 다크 모드 스타일 */
}
```

색상을 추가하거나 변경할 때는 하드코딩된 색상값 대신 디자인 토큰을 사용합니다.

주요 색상 규칙:

- `--pine`: 완료(Completed) 상태 전용 색상
- `--focus`: 키보드 포커스 링(Focus Ring) 색상

### 4-5. 폰트

기본 폰트는 IBM Plex Sans KR을 사용합니다.

Google Fonts에서 불러오며 설정 위치는 다음과 같습니다.

```text
index.html
```

---

## 5. 접근성 규칙 (Accessibility)

기존 접근성 동작은 UI 개선 및 리팩토링 과정에서도 반드시 유지해야 합니다.

### 5-1. 체크박스

체크박스는 네이티브 HTML 요소를 사용합니다.

```html
<input type="checkbox">
```

CSS의 다음 속성으로 기본 외형을 변경합니다.

```css
appearance: none;
```

작업 텍스트는 해당 체크박스의 `<label>`로 연결합니다.

### 5-2. 포커스 관리

편집 모드에서 저장 또는 취소한 후에는 해당 작업의 "수정" 버튼으로 포커스를 복귀시킵니다.

관련 구현:

```text
TodoItem
returnFocus
```

작업을 삭제한 후에는 새로운 ToDo 입력 필드로 포커스를 이동합니다.

관련 구현:

```text
App → TodoInput
inputRef
```

Esc 키를 누르면 편집 모드를 취소합니다.

### 5-3. 스크린 리더 지원

각 작업의 버튼에는 작업 내용을 포함하는 `aria-label`을 제공합니다.

진행률 안내 텍스트는 `aria-live` 영역을 사용하여 변경 사항을 보조 기술에 전달합니다.

### 5-4. 모바일 접근성

화면 너비가 360px 이상일 때는 작업 버튼을 한 줄에 배치합니다.

359px 이하에서는 다음 미디어 쿼리를 적용하여 버튼이 줄바꿈되도록 처리합니다.

```css
@media (max-width: 359px) {
  /* 작은 화면의 버튼 줄바꿈 */
}
```

---

## 6. UI 디자인 규칙 (UI Guidelines)

UI 작업을 수행할 때는 다음 문서를 반드시 참고합니다.

```text
docs/ui-guidelines.md
```

UI가 변경되면 해당 문서도 함께 업데이트합니다.

### 6-1. 디자인 시스템

새로운 컴포넌트는 정의된 다음 규칙을 따라야 합니다.

- Color System: 색상 체계
- Typography: 글꼴 및 텍스트 규칙
- Spacing: 간격 체계
- Component Rules: 컴포넌트 규칙
- Responsive Breakpoints: 반응형 기준
- Accessibility Rules: 접근성 규칙

### 6-2. 컴포넌트 일관성

작업 카드(Task Card)와 작업 입력 폼(Task Form)은 공통 디자인 토큰을 사용합니다.

새로운 컴포넌트를 추가할 때도 기존 디자인 시스템을 재사용합니다.

### 6-3. 반응형 및 접근성

모든 UI 변경 작업은 다음 사항을 고려해야 합니다.

- 데스크톱 화면
- 태블릿 화면
- 모바일 화면
- 키보드 접근성
- 스크린 리더 지원

### 6-4. 기존 기능 유지

UI 개선 과정에서 기존 CRUD 기능을 유지해야 합니다.

UI 변경 후에는 추가, 조회, 수정, 삭제 및 완료 상태 변경 기능을 검증합니다.

---

## 7. 개발 환경 및 주의 사항 (Notes)

### 7-1. Windows 브라우저 화면 캡처

현재 Windows 환경의 Headless Chrome/Edge에서는 약 500px보다 작은 브라우저 창이 정상적으로 렌더링되지 않을 수 있습니다.

따라서 다음과 같이 설정해도 실제 390px 화면 캡처가 잘릴 수 있습니다.

```bash
--window-size=390,...
```

실제 모바일 너비의 화면을 캡처하려면 동일 출처(Same-Origin) 페이지에서 너비 390px의 `<iframe>`을 사용합니다.

예를 들어 다음 디렉터리에 임시 HTML 파일을 생성할 수 있습니다.

```text
frontend/public/
```

화면 캡처와 검증이 끝나면 임시 파일을 삭제합니다.

### 7-2. OMC 로컬 상태

다음 디렉터리는 OMC의 로컬 도구 상태를 저장합니다.

```text
.omc/
```

이 디렉터리는 Git 저장소에 커밋하지 않습니다.

필요한 경우 `.gitignore`에 등록하여 추적되지 않도록 관리합니다.

---

## 8. Claude Code 작업 원칙

### 8-1. 작업 시작 전

1. 프로젝트 구조를 확인한다.
2. `README.md`와 관련 문서를 확인한다.
3. 기존 코드의 동작을 분석한다.
4. 변경 대상과 영향을 받는 기능을 파악한다.
5. 필요한 경우 작업 계획을 한국어로 작성한다.

### 8-2. 작업 수행 중

1. 기존 프로젝트 구조와 코딩 규칙을 유지한다.
2. 불필요한 파일 변경을 최소화한다.
3. 기존 CRUD 기능을 훼손하지 않는다.
4. UI 변경 시 `docs/ui-guidelines.md`를 참고한다.
5. 변경 사항과 주요 의사결정을 한국어로 설명한다.

### 8-3. 작업 완료 후

1. 변경된 파일을 확인한다.
2. 가능한 범위에서 빌드 및 정적 검사를 수행한다.
3. 기존 기능에 대한 영향을 검증한다.
4. 오류가 있다면 원인과 해결 방법을 한국어로 설명한다.
5. 최종 작업 결과를 한국어로 요약한다.

### 8-4. 최종 보고 형식

작업 완료 시 가능한 한 다음 형식을 따른다.

#### 작업 요약
- 수행한 작업을 한국어로 설명한다.

#### 변경 파일
- 변경된 파일과 변경 이유를 정리한다.

#### 검증 결과
- 실행한 검사와 결과를 설명한다.

#### 남은 작업
- 미완료 항목이나 추가 개선 사항을 정리한다.

모든 보고 내용은 한국어로 작성한다.
