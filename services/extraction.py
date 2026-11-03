
import json
import os
import time

from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel

MAX_ATTEMPTS = 3


class ResearchExtraction(BaseModel):
    summary: str
    key_entities: list[str]


def extract_research(abstract: str) -> tuple[ResearchExtraction, int | None, float]:
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not configured.",
        )

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=60.0,
            max_retries=3,
        )

        for attempt in range(1, MAX_ATTEMPTS + 1):
            start_time = time.perf_counter()

            response = client.chat.completions.create(
                model="openrouter/free",
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

    except HTTPException:
        raise
    except Exception as exc:
        print(
            f"OpenRouter error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        raise HTTPException(
            status_code=502,
            detail="OpenRouter extraction failed. "
                   "Check the server terminal for details.",
        ) from exc
