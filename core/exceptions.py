# Level 2: the app's own error types.
# Clients, services and repositories raise these instead of fastapi.HTTPException,
# so they don't depend on HTTP and can be reused from a script, a Celery worker
# (Level 6) or an Airflow task (Level 7). The web layer turns each one into a
# status code in a single place (see ERROR_STATUS_CODES in main.py).


class SynthError(Exception):
    """Base class for every expected Synth error. The message is safe to show users."""


# ---- requests and documents (raised by services) ----

class InvalidExtractionRequestError(SynthError):
    """POST /extract got both or neither of abstract and arxiv_id."""


class DocumentNotFoundError(SynthError):
    """No document exists with the requested id."""


# ---- arXiv ----

class InvalidArxivIdError(SynthError):
    """arXiv rejected the ID's format (e.g. "not-an-id")."""


class ArxivPaperNotFoundError(SynthError):
    """The ID is well formed, but arXiv has no paper (or no abstract) for it."""


class ArxivUnavailableError(SynthError):
    """arXiv couldn't be reached or returned an unexpected error."""


# ---- LLM ----

class LLMNotConfiguredError(SynthError):
    """OPENROUTER_API_KEY is missing, so no LLM call can be made."""


class LLMExtractionError(SynthError):
    """The LLM call failed or never returned usable JSON."""
