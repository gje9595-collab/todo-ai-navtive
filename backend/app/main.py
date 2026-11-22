"""FastAPI 진입점. 실행: `uvicorn app.main:app --reload` (backend/에서)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings, validate_settings
from app.core.errors import register_exception_handlers
from app.repositories.todo_repository import InMemoryTodoRepository, TodoRepository
from app.routers import todos
from app.schemas.todo import HealthResponse


def _create_repository(settings: Settings) -> TodoRepository:
    """1단계는 In-Memory 저장소만 쓴다. Supabase 저장소는 2단계(T-23)에서 이 함수에 추가한다."""
    return InMemoryTodoRepository()


def create_app(settings: Settings | None = None) -> FastAPI:
    """앱을 만든다. 테스트는 호출할 때마다 빈 저장소를 가진 새 앱을 받는다."""
    settings = settings or get_settings()
    validate_settings(settings)

    app = FastAPI(title="My ToDo API", version="1.0.0")
    app.state.todo_repository = _create_repository(settings)

    # API 명세 4절: 허용 Origin은 환경 변수로만 정하고 와일드카드는 쓰지 않는다.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_exception_handlers(app)

    app.include_router(todos.router, prefix="/api")

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        """배포 확인용. 인증이 필요 없고 저장소 연결은 검사하지 않는다 (NFR-005)."""
        return HealthResponse(status="ok")

    return app


app = create_app()
