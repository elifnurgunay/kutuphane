from enum import StrEnum

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.validation_messages import translate


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    USER_INACTIVE = "USER_INACTIVE"
    FORBIDDEN = "FORBIDDEN"
    WRONG_PASSWORD = "WRONG_PASSWORD"
    SETTING_MISSING = "SETTING_MISSING"
    NAME_EXISTS = "NAME_EXISTS"
    ISBN_EXISTS = "ISBN_EXISTS"
    INVALID_ISBN = "INVALID_ISBN"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    ENTITY_IN_USE = "ENTITY_IN_USE"
    CATEGORY_CYCLE = "CATEGORY_CYCLE"
    COPY_STATUS_LOCKED = "COPY_STATUS_LOCKED"
    EMAIL_EXISTS = "EMAIL_EXISTS"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    MEMBERSHIP_EXPIRED = "MEMBERSHIP_EXPIRED"
    LOAN_NOT_ACTIVE = "LOAN_NOT_ACTIVE"
    LOAN_OVERDUE = "LOAN_OVERDUE"
    RESERVATION_PENDING = "RESERVATION_PENDING"
    RESERVATION_NOT_ACTIVE = "RESERVATION_NOT_ACTIVE"
    ALREADY_BORROWED = "ALREADY_BORROWED"
    FINE_NOT_UNPAID = "FINE_NOT_UNPAID"
    MEMBER_INACTIVE = "MEMBER_INACTIVE"
    LOAN_LIMIT_EXCEEDED = "LOAN_LIMIT_EXCEEDED"
    UNPAID_FINES = "UNPAID_FINES"
    HAS_OVERDUE = "HAS_OVERDUE"
    COPY_NOT_AVAILABLE = "COPY_NOT_AVAILABLE"
    RENEW_LIMIT = "RENEW_LIMIT"
    RESERVATION_EXISTS = "RESERVATION_EXISTS"
    BOOK_AVAILABLE_NO_RESERVATION = "BOOK_AVAILABLE_NO_RESERVATION"


class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


_HTTP_STATUS_CODES = {
    401: (ErrorCode.NOT_AUTHENTICATED, "Oturum açmanız gerekiyor."),
    403: (ErrorCode.FORBIDDEN, "Bu işlem için yetkiniz yok."),
    404: (ErrorCode.NOT_FOUND, "Kayıt bulunamadı."),
    405: ("METHOD_NOT_ALLOWED", "Bu işlem desteklenmiyor."),
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        details = translate(list(exc.errors()))
        message = details[0]["message"] if details else "Gönderilen veri geçersiz."
        body = error_body(ErrorCode.VALIDATION_ERROR, message)
        body["error"]["details"] = details
        return JSONResponse(body, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_STATUS_CODES.get(exc.status_code, ("HTTP_ERROR", "İstek işlenemedi."))
        return JSONResponse(error_body(code, message), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unexpected(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            error_body("INTERNAL_ERROR", "Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."),
            status_code=500,
        )
