"""FastAPI 진입점. 실행: `uvicorn app.main:app --reload` (backend/ 에서)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import SUPPORTED_AUTH_MODES, Settings, get_settings
from app.core.errors import register_exception_handlers
from app.repositories.todo_repository import InMemoryTodoRepository
from app.routers import todos


def create_app(settings: Settings | None = None) -> FastAPI:
    """앱을 만듭니다. 테스트는 호출할 때마다 비어 있는 저장소를 가진 새 앱을 받습니다."""
    settings = settings or get_settings()
    if settings.auth_mode not in SUPPORTED_AUTH_MODES:
        raise RuntimeError(
            f"AUTH_MODE={settings.auth_mode!r}는 아직 지원하지 않습니다. 지원 값: {SUPPORTED_AUTH_MODES}"
        )

    app = FastAPI(title="todo-ai-native API", version="0.1.0")
    app.state.todo_repository = InMemoryTodoRepository()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_exception_handlers(app)

    app.include_router(todos.router, prefix="/api")

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
