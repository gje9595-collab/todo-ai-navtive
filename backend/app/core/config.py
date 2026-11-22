"""애플리케이션 설정. 값은 환경 변수에서 읽고, 잘못된 조합이면 앱 생성 시 실패시킨다 (API 명세 1절, 1-1절)."""

import os
from dataclasses import dataclass

DEFAULT_CORS_ORIGINS = "http://localhost:5173"

# API 명세 1절의 인증 모드. `supabase`(JWT 검증)는 3단계(T-41)에서 구현한다.
KNOWN_AUTH_MODES = ("dev", "supabase")
IMPLEMENTED_AUTH_MODES = ("dev",)


@dataclass(frozen=True)
class Settings:
    """서버 설정 값 묶음. 테스트에서는 직접 만들어 `create_app(settings)`에 넘긴다."""

    cors_origins: tuple[str, ...] = (DEFAULT_CORS_ORIGINS,)
    auth_mode: str = "dev"
    supabase_url: str = ""
    supabase_secret_key: str = ""
    # Vercel 서버리스 환경 여부 (`VERCEL=1`)
    is_vercel: bool = False


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def get_settings() -> Settings:
    """환경 변수로부터 설정을 만든다."""
    return Settings(
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)),
        auth_mode=os.getenv("AUTH_MODE", "dev").strip(),
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_secret_key=os.getenv("SUPABASE_SECRET_KEY", "").strip(),
        is_vercel=os.getenv("VERCEL") == "1",
    )


def validate_settings(settings: Settings) -> None:
    """허용되지 않는 설정이면 RuntimeError를 발생시켜 서버 시작을 막는다 (AC-FR-007-3, AC-NFR-004-1)."""
    if settings.auth_mode not in KNOWN_AUTH_MODES:
        raise RuntimeError(f"AUTH_MODE={settings.auth_mode!r}는 지원하지 않습니다. 사용 가능한 값: {KNOWN_AUTH_MODES}")
    if settings.auth_mode not in IMPLEMENTED_AUTH_MODES:
        raise RuntimeError(f"AUTH_MODE={settings.auth_mode!r}는 아직 구현되지 않았습니다(3단계 T-41). 지금은 'dev'를 사용하세요.")

    has_url = bool(settings.supabase_url)
    has_key = bool(settings.supabase_secret_key)
    if has_url != has_key:
        raise RuntimeError("SUPABASE_URL과 SUPABASE_SECRET_KEY는 둘 다 설정하거나 둘 다 비워야 합니다.")
    if has_url and has_key:
        raise RuntimeError("Supabase 저장소는 아직 구현되지 않았습니다(2단계 T-23). 지금은 두 값을 비워 In-Memory 저장소를 사용하세요.")
    if settings.is_vercel:
        raise RuntimeError("Vercel 환경에서는 In-Memory 저장소를 쓸 수 없습니다. SUPABASE_URL과 SUPABASE_SECRET_KEY를 설정하세요.")
