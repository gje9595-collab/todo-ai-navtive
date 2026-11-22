"""요청 사용자 식별 (API 명세 1절, FR-007).

1단계는 개발용(dev) 인증만 지원한다.
- `Authorization: Bearer <token>`이 없거나 형식이 틀리면 401을 반환한다.
- 토큰 값(앞뒤 공백 제거, 1~128자)을 서명 검증 없이 그대로 user_id로 쓴다. **공개 배포 금지 (PRD D-4).**

3단계(T-41)에서 이 의존성만 Supabase JWT 검증(`sub` 클레임 → user_id)으로 교체하면
Router, Service, Repository는 바꿀 필요가 없다.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.core.errors import UnauthenticatedError

DEV_TOKEN_MAX_LENGTH = 128


def get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> str:
    """Authorization 헤더에서 user_id를 꺼낸다.

    FastAPI는 하위 의존성(이 함수)을 본문 스키마 검증보다 먼저 실행하므로,
    인증 오류(401)가 본문 검증 오류(422)보다 우선한다 (AC-FR-007-2).
    """
    if not authorization:
        raise UnauthenticatedError()

    scheme, _, token = authorization.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise UnauthenticatedError("Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.")
    if len(token) > DEV_TOKEN_MAX_LENGTH:
        raise UnauthenticatedError(f"토큰은 {DEV_TOKEN_MAX_LENGTH}자 이하여야 합니다.")

    return token


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
