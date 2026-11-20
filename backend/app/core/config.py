"""애플리케이션 설정. 값은 환경 변수에서 읽습니다."""

import os
from dataclasses import dataclass

DEFAULT_CORS_ORIGINS = "http://localhost:5173"
SUPPORTED_AUTH_MODES = ("dev",)


@dataclass(frozen=True)
class Settings:
    """서버 설정 값 묶음."""

    cors_origins: tuple[str, ...]
    # dev: 개발용 인증(토큰 값을 그대로 user_id로 사용). Supabase JWT 검증은 추후 추가 예정.
    auth_mode: str = "dev"


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def get_settings() -> Settings:
    """환경 변수로부터 설정을 만듭니다."""
    return Settings(
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)),
        auth_mode=os.getenv("AUTH_MODE", "dev"),
    )
