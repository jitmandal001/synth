# Level 2: the ONE place that decides which HTTP status each app error gets.
# Clients and services raise plain Python errors (core/exceptions.py); this turns
# them into responses with the same codes and {"detail": "..."} body that
# fastapi.HTTPException used to produce. Moved here from main.py.
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import (
    ArxivPaperNotFoundError,
    ArxivUnavailableError,
    DocumentNotFoundError,
    InvalidArxivIdError,
    InvalidExtractionRequestError,
    LLMExtractionError,
    LLMNotConfiguredError,
    SynthError,
)

ERROR_STATUS_CODES: dict[type[SynthError], int] = {
    InvalidExtractionRequestError: 400,
    DocumentNotFoundError: 404,
    InvalidArxivIdError: 400,
    ArxivPaperNotFoundError: 404,
    ArxivUnavailableError: 502,
    LLMNotConfiguredError: 500,
    LLMExtractionError: 502,
}


async def synth_error_handler(request: Request, exc: SynthError) -> JSONResponse:
    status_code = ERROR_STATUS_CODES.get(type(exc), 500)  # unknown SynthError -> 500
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SynthError, synth_error_handler)
