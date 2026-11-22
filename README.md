# todo-ai-native

React, FastAPI, Supabase, Vercel로 만드는 ToDo List 웹 애플리케이션입니다.

> 현재 상태: ToDo CRUD(React + FastAPI)와 Supabase PostgreSQL 저장소가 구현되어 있습니다. 인증은 개발용 `dev` 모드입니다.

## 프로젝트 목적

- 할 일을 추가, 조회, 수정, 완료 처리, 삭제할 수 있는 ToDo List 서비스를 만듭니다.
- 프론트엔드(React)와 백엔드(FastAPI)를 나누고, 데이터 저장과 인증은 Supabase에 맡깁니다.
- 프론트엔드와 백엔드 모두 Vercel에 배포합니다.
- 작은 단위의 브랜치와 커밋으로 기능을 하나씩 추가합니다.

## 기술 스택

| 영역 | 기술 | 역할 |
| --- | --- | --- |
| Frontend | React (Vite, TypeScript) | 사용자 화면, API 호출 |
| Backend | FastAPI (Python) | REST API, 비즈니스 로직, 입력 검증 |
| Database / Auth | Supabase (PostgreSQL, Supabase Auth) | ToDo 데이터 저장, 사용자 인증 |
| Deployment | Vercel | 프론트엔드 정적 호스팅, FastAPI 서버리스 함수 |

## 초기 디렉터리 구조

```
todo-ai-native/
├── frontend/              # React 앱 (Vite)
│   ├── public/
│   ├── src/
│   │   ├── components/    # 재사용 UI 컴포넌트
│   │   ├── pages/         # 화면 단위 컴포넌트
│   │   ├── api/           # 백엔드 API 호출 모듈
│   │   └── lib/           # Supabase 클라이언트 등 공통 유틸
│   └── package.json
├── backend/               # FastAPI 앱
│   ├── app/
│   │   ├── main.py        # FastAPI 진입점
│   │   ├── routers/       # API 라우터 (todos 등)
│   │   ├── schemas/       # Pydantic 요청/응답 모델
│   │   ├── services/      # 비즈니스 로직
│   │   ├── repositories/  # 데이터 저장소 (현재 In-Memory, 추후 Supabase)
│   │   ├── models/        # 도메인 모델
│   │   └── core/          # 설정, 인증, 공통 에러 처리
│   ├── tests/
│   └── requirements.txt
├── supabase/
│   └── migrations/        # DB 스키마 마이그레이션 SQL
├── docs/                  # 설계 문서
├── .gitignore
└── README.md
```

위 구조는 계획이며, 각 디렉터리는 해당 기능을 구현할 때 만듭니다.

## 브랜치 전략

- `main`: 배포 가능한 안정 브랜치
- `feature/*`: 기능 개발 브랜치 (현재 브랜치: `feature/todo-init`)

## 환경 변수

| 이름 | 사용처 | 설명 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | frontend | FastAPI 서버 주소 (`/api`는 붙이지 않음) |
| `VITE_DEV_AUTH_TOKEN` | frontend | dev 인증 토큰 (기본 `dev-user`) |
| `CORS_ORIGINS` | backend | 허용할 프론트엔드 Origin, 쉼표 구분 |
| `AUTH_MODE` | backend | 현재 `dev`만 지원 |
| `SUPABASE_URL` | backend | Supabase 프로젝트 주소 (`https://<ref>.supabase.co`) |
| `SUPABASE_SECRET_KEY` | backend | 서버 전용 Secret Key(`sb_secret_...`). RLS를 우회하므로 커밋·프론트엔드 노출 금지 |

`SUPABASE_URL`, `SUPABASE_SECRET_KEY`를 둘 다 비우면 In-Memory 저장소를 사용합니다.

## Supabase 설정

1. Supabase 대시보드에서 프로젝트를 만듭니다.
2. **SQL Editor**에서 `supabase/migrations/`의 `0001` → `0002` → `0003` 파일을 순서대로 실행합니다.
   `0003`은 백엔드가 쓰는 `service_role`에 테이블 권한을 부여합니다. 빠지면 API가 `permission denied`로 500을 반환합니다.
3. **Project Settings → API Keys**에서 Project URL과 Secret Key를 `SUPABASE_URL`, `SUPABASE_SECRET_KEY`로 사용합니다.
   백엔드는 Supabase REST API(HTTPS)로 접속하므로 서버리스(Vercel)에서도 DB 연결 수를 관리할 필요가 없습니다.

로컬에서 Supabase에 연결해 실행하려면 `backend/.env`에 두 값을 넣고 다음과 같이 실행합니다.

```bash
cd backend
uvicorn app.main:app --reload --env-file .env
```

## 배포 (Vercel)

`backend/`와 `frontend/`를 **각각 별도의 Vercel 프로젝트**로 배포합니다.

| 프로젝트 | Root Directory | 설정 파일 | 환경 변수 |
| --- | --- | --- | --- |
| 백엔드 | `backend` | `vercel.json`(모든 경로 → `api/index.py`), `.python-version` | `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `CORS_ORIGINS`(프론트엔드 배포 주소), `AUTH_MODE=dev` |
| 프론트엔드 | `frontend` | `vercel.json`(Vite) | `VITE_API_BASE_URL`(백엔드 배포 주소), `VITE_DEV_AUTH_TOKEN` |

순서:

1. 백엔드를 먼저 배포하고 주소(예: `https://todo-api-xxx.vercel.app`)를 확인합니다.
2. 프론트엔드에 `VITE_API_BASE_URL`을 백엔드 주소로 설정해 배포합니다. `VITE_*` 값은 빌드 시점에 포함되므로 변경 후 재배포가 필요합니다.
3. 백엔드의 `CORS_ORIGINS`에 프론트엔드 주소를 넣고 재배포합니다.

```bash
# CLI로 배포하는 경우 (각 디렉터리에서)
npx vercel link
npx vercel env add SUPABASE_URL production
npx vercel env add SUPABASE_SECRET_KEY production
npx vercel deploy --prod
```

> 주의: dev 인증은 토큰 값을 그대로 user_id로 사용하므로, 공개 배포 시 누구나 다른 토큰으로 요청할 수 있습니다.
> 실제 사용자 데이터를 다루기 전에 Supabase Auth(JWT 검증)를 도입해야 합니다.
