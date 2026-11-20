"""요청 사용자 식별 (API 명세 1절).

현재는 개발용(dev) 인증만 지원합니다.
- `Authorization: Bearer <token>` 헤더가 없거나 형식이 틀리면 401을 반환합니다.
- 토큰 값을 서명 검증 없이 그대로 user_id로 사용합니다. **운영 환경에서 사용하면 안 됩니다.**

Supabase 연동 시 이 의존성만 JWT 검증(`sub` 클레임 → user_id)으로 교체하면
Router/Service/Repository는 수정할 필요가 없습니다.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.core.errors import UnauthenticatedError


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Authorization 헤더에서 user_id를 꺼냅니다. 비즈니스 로직보다 먼저 실행됩니다(AC-NFR-004-2)."""
    if not authorization:
        raise UnauthenticatedError()

    scheme, _, token = authorization.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise UnauthenticatedError("Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.")

    return token


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
