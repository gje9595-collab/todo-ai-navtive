"""API 명세 2-1절의 공통 에러 응답 포맷과 예외 처리기."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """서비스 계층에서 발생시키는 도메인 에러의 기본 클래스."""

    status_code = 500
    code = "INTERNAL_ERROR"
    default_message = "서버 내부 오류가 발생했습니다."

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
    """`{"error": {code, message, details}}` 형태의 응답을 만듭니다."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    # pydantic 에러에는 JSON 직렬화가 안 되는 객체(ctx)가 섞여 있어 필요한 값만 추립니다.
    details = []
    for err in exc.errors():
        if err.get("type") == "json_invalid":
            # loc에 문자 위치(숫자)가 들어오므로 필드 대신 본문 전체 오류로 안내합니다.
            details.append({"field": "", "message": "요청 본문이 올바른 JSON 형식이 아닙니다."})
            continue
        field = ".".join(str(part) for part in err.get("loc", ()) if part != "body")
        message = str(err.get("msg", "")).removeprefix("Value error, ")
        details.append({"field": field, "message": message})
    return details


_HTTP_ERRORS = {
    # 잘못된 JSON, UTF-8이 아닌 본문 등 본문 자체를 해석하지 못한 경우
    400: ("BAD_REQUEST", "요청 본문을 해석할 수 없습니다. UTF-8 JSON 형식인지 확인해 주세요."),
    404: ("NOT_FOUND", "요청한 경로를 찾을 수 없습니다."),
    405: ("METHOD_NOT_ALLOWED", "허용되지 않는 HTTP 메서드입니다."),
}


def register_exception_handlers(app: FastAPI) -> None:
    """모든 에러가 공통 포맷으로 응답되도록 처리기를 등록합니다."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = _validation_details(exc)
        message = details[0]["message"] if details else "요청 형식이 올바르지 않습니다."
        return error_response(422, "VALIDATION_ERROR", message, details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", str(exc.detail)))
        return error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
        return error_response(500, AppError.code, AppError.default_message)
