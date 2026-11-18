# Level 2: moved from services/extraction.py. Talks to the OpenRouter LLM only;
# raises core.exceptions errors instead of fastapi.HTTPException.
#
# POST /extract path, step 9 of 10: turn the abstract into summary + key_entities.
# Runs in a worker thread (asyncio.to_thread) because the OpenAI client blocks.
import json
import time

from openai import OpenAI

from core.config import get_settings
from core.exceptions import LLMExtractionError, LLMNotConfiguredError
# Level 2: the LLM output shape moved to schemas/ with the other API schemas.
from schemas.extraction import ResearchExtraction

MAX_ATTEMPTS = 3                                  # retries when the model returns bad JSON


def extract_research(abstract: str) -> tuple[ResearchExtraction, int | None, float]:
    # Level 2: key, base URL and model come from Settings, not os.getenv/hardcoded.
    settings = get_settings()

    # Missing OR empty (OPENROUTER_API_KEY=) both count as "not configured",
    # matching Level 1's `if not api_key` check.
    key = settings.openrouter_api_key
    if key is None or not key.get_secret_value():
        raise LLMNotConfiguredError("OPENROUTER_API_KEY is not configured.")   # → 500

    try:
        client = OpenAI(                                    # OpenAI-compatible client pointed at OpenRouter
            base_url=settings.openrouter_base_url,
            api_key=key.get_secret_value(),                 # the real key, only here
            timeout=60.0,                                   # give up on one call after 60 s
            max_retries=3,                                  # client retries network/429 errors itself
        )

        for attempt in range(1, MAX_ATTEMPTS + 1):          # up to 3 tries for usable output
            start_time = time.perf_counter()                # start the latency timer

            response = client.chat.completions.create(      # the LLM call (slowest part, ~10 s)
                model=settings.llm_model,                   # e.g. "openrouter/free"
                messages=[
                    {
                        "role": "system",                   # instructions for the model
                        "content": (
                            "Analyze research paper abstracts. "
                            "Return JSON with exactly two fields: "
                            "summary (string) and key_entities (array "
                            "of strings). Use only information supported "
                            "by the abstract."
                        ),
                    },
                    {"role": "user", "content": abstract},  # the actual abstract
                ],
                response_format={"type": "json_object"},    # ask for JSON only
                max_tokens=4000,                            # cap on reply length
                temperature=0.2,                            # low = more consistent answers
                extra_body={"reasoning": {"effort": "low"}},  # keep reasoning models short
            )

            latency = time.perf_counter() - start_time      # seconds the call took
            choice = response.choices[0]                    # the model's answer

            try:
                if not choice.message.content:              # empty reply
                    raise ValueError(
                        f"Empty model response "
                        f"(finish_reason={choice.finish_reason})"
                    )

                data = json.loads(choice.message.content)          # text → dict (ValueError if not JSON)
                result = ResearchExtraction.model_validate(data)   # dict → checked object (ValueError if wrong shape)

                usage = response.usage                      # token counts, if the provider sent them
                token_count = (
                    usage.total_tokens if usage is not None else None
                )

                return result, token_count, latency         # success → back to the service

            except ValueError as exc:                       # bad output: log it and try again
                print(
                    f"OpenRouter attempt {attempt}/{MAX_ATTEMPTS} "
                    f"({response.model}) gave unusable output: {exc}",
                    flush=True,
                )

        raise ValueError(                                   # all 3 attempts failed
            f"No usable output after {MAX_ATTEMPTS} attempts"
        )

    except Exception as exc:
        # The real cause goes to the server terminal; the user gets a safe message.
        print(
            f"OpenRouter error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        raise LLMExtractionError(                           # → 502
            "OpenRouter extraction failed. "
            "Check the server terminal for details."
        ) from exc
