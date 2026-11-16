# Level 2: moved from services/extraction.py. Talks to the OpenRouter LLM only;
# raises core.exceptions errors instead of fastapi.HTTPException.
import json
import time

from openai import OpenAI

from core.config import get_settings
from core.exceptions import LLMExtractionError, LLMNotConfiguredError
# Level 2: the LLM output shape moved to schemas/ with the other API schemas.
from schemas.extraction import ResearchExtraction

MAX_ATTEMPTS = 3


def extract_research(abstract: str) -> tuple[ResearchExtraction, int | None, float]:
    # Level 2: key, base URL and model come from Settings, not os.getenv/hardcoded.
    settings = get_settings()

    # Missing OR empty (OPENROUTER_API_KEY=) both count as "not configured",
    # matching Level 1's `if not api_key` check.
    key = settings.openrouter_api_key
    if key is None or not key.get_secret_value():
        raise LLMNotConfiguredError("OPENROUTER_API_KEY is not configured.")

    try:
        client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=key.get_secret_value(),
            timeout=60.0,
            max_retries=3,
        )

        for attempt in range(1, MAX_ATTEMPTS + 1):
            start_time = time.perf_counter()

            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Analyze research paper abstracts. "
                            "Return JSON with exactly two fields: "
                            "summary (string) and key_entities (array "
                            "of strings). Use only information supported "
                            "by the abstract."
                        ),
                    },
                    {"role": "user", "content": abstract},
                ],
                response_format={"type": "json_object"},
                max_tokens=4000,
                temperature=0.2,
                extra_body={"reasoning": {"effort": "low"}},
            )

            latency = time.perf_counter() - start_time
            choice = response.choices[0]

            try:
                if not choice.message.content:
                    raise ValueError(
                        f"Empty model response "
                        f"(finish_reason={choice.finish_reason})"
                    )

                data = json.loads(choice.message.content)
                result = ResearchExtraction.model_validate(data)

                usage = response.usage
                token_count = (
                    usage.total_tokens if usage is not None else None
                )

                return result, token_count, latency

            except ValueError as exc:
                print(
                    f"OpenRouter attempt {attempt}/{MAX_ATTEMPTS} "
                    f"({response.model}) gave unusable output: {exc}",
                    flush=True,
                )

        raise ValueError(
            f"No usable output after {MAX_ATTEMPTS} attempts"
        )

    except Exception as exc:
        # The real cause goes to the server terminal; the user gets a safe message.
        print(
            f"OpenRouter error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        raise LLMExtractionError(
            "OpenRouter extraction failed. "
            "Check the server terminal for details."
        ) from exc
