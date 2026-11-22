"""공통 에러 응답 포맷과 예외 처리기 (API 명세 2-1절, NFR-006).

모든 에러는 `{"error": {"code", "message", "details"}}` 형태로 응답한다.
메시지는 사용자에게 그대로 보여 줄 수 있는 한국어 문장이며, 내부 정보(스택, SQL, 키)는 넣지 않는다 (NFR-004).
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """서비스·인증 계층에서 발생시키는 도메인 에러의 기본 클래스."""

    status_code = 500
    code = "INTERNAL_ERROR"
    default_message = "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class UnauthenticatedError(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"
    default_message = "인증이 필요합니다."


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    default_message = "이 할 일에 접근할 권한이 없습니다."


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    default_message = "할 일을 찾을 수 없습니다."


def error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


# pydantic 오류 유형 → 한국어 메시지. 목록에 없는 유형은 기본 문구를 쓴다.
_VALIDATION_MESSAGES = {
    "missing": "필수 항목입니다.",
    "string_type": "문자열이어야 합니다.",
    "bool_type": "true 또는 false여야 합니다.",
    "extra_forbidden": "정의되지 않은 항목입니다.",
    "uuid_parsing": "올바른 UUID 형식이 아닙니다.",
    "uuid_type": "올바른 UUID 형식이 아닙니다.",
    "model_attributes_type": "JSON 객체여야 합니다.",
    "dict_type": "JSON 객체여야 합니다.",
    "json_invalid": "요청 본문이 올바른 JSON 형식이 아닙니다.",
}
_DEFAULT_VALIDATION_MESSAGE = "요청 형식이 올바르지 않습니다."


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    """pydantic 오류를 `[{field, message}]`로 바꾼다. 원본에는 직렬화할 수 없는 값(ctx)이 섞여 있다."""
    details = []
    for err in exc.errors():
        err_type = err.get("type", "")
        if err_type == "json_invalid":
            # loc에 문자 위치(숫자)가 들어오므로 필드 대신 본문 전체 오류로 안내한다.
            details.append({"field": "", "message": _VALIDATION_MESSAGES["json_invalid"]})
            continue
        # 위치 접두사(body/path/query)는 빼고 필드 이름만 남긴다. 예: ("query", "category") → "category" (AC-FR-014-3)
        field = ".".join(str(part) for part in err.get("loc", ()) if part not in ("body", "path", "query"))
        if err_type == "value_error":
            # 스키마의 validator가 직접 만든 한국어 메시지
            message = str(err.get("msg", "")).removeprefix("Value error, ")
        else:
            message = _VALIDATION_MESSAGES.get(err_type, _DEFAULT_VALIDATION_MESSAGE)
        details.append({"field": field, "message": message})
    return details


# 프레임워크 수준 오류 (경로 없음, 메서드 불가, 본문 해석 불가)
_HTTP_ERRORS = {
    400: ("BAD_REQUEST", "요청 본문을 해석할 수 없습니다. UTF-8 JSON 형식인지 확인해 주세요."),
    404: ("NOT_FOUND", "요청한 경로를 찾을 수 없습니다."),
    405: ("METHOD_NOT_ALLOWED", "허용되지 않는 HTTP 메서드입니다."),
}


def register_exception_handlers(app: FastAPI) -> None:
    """모든 에러가 공통 포맷으로 응답되도록 처리기를 등록한다."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI는 깨진 JSON을 인증 의존성보다 먼저 파싱한다. 인증 우선 규칙(api-spec 1절)을 지키려고
        # 보호된 경로에서는 인증을 먼저 확인한다. (순환 import를 피하려고 함수 안에서 가져온다.)
        if request.url.path.startswith("/api/todos"):
            from app.core.auth import get_current_user_id

            try:
                get_current_user_id(request.headers.get("authorization"))
            except UnauthenticatedError as auth_error:
                return error_response(auth_error.status_code, auth_error.code, auth_error.message)

        details = _validation_details(exc)
        message = details[0]["message"] if details else _DEFAULT_VALIDATION_MESSAGE
        return error_response(422, "VALIDATION_ERROR", message, details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "요청을 처리할 수 없습니다."))
        return error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # 원인은 서버 로그에만 남기고, 응답에는 일반 문구만 보낸다 (AC-NFR-004-3).
        logger.exception("처리되지 않은 예외: %s %s", request.method, request.url.path, exc_info=exc)
        return error_response(500, AppError.code, AppError.default_message)
