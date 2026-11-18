# Level 2: the ONE place that decides which HTTP status each app error gets.
# Clients and services raise plain Python errors (core/exceptions.py); this turns
# them into responses with the same codes and {"detail": "..."} body that
# fastapi.HTTPException used to produce. Moved here from main.py.
#
# POST /extract path, step 10 of 10 (only when something fails):
# a SynthError raised in steps 6-9 travels up past the route and lands here.
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

ERROR_STATUS_CODES: dict[type[SynthError], int] = {   # error type → HTTP status
    InvalidExtractionRequestError: 400,                # both/neither input
    DocumentNotFoundError: 404,                        # (GET /documents/{id})
    InvalidArxivIdError: 400,                          # "not-an-id"
    ArxivPaperNotFoundError: 404,                      # no such paper / no abstract
    ArxivUnavailableError: 502,                        # arXiv down
    LLMNotConfiguredError: 500,                        # no API key
    LLMExtractionError: 502,                           # LLM failed
}


async def synth_error_handler(request: Request, exc: SynthError) -> JSONResponse:
    status_code = ERROR_STATUS_CODES.get(type(exc), 500)  # unknown SynthError -> 500
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})  # e.g. {"detail": "..."}


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SynthError, synth_error_handler)  # called from main.py at startup
