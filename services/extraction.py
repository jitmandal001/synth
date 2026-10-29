
import json
import os

from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel

# openrouter/free sends each call to a randomly chosen free model, and
# some of them reply with empty or non-JSON output, so those are retried.
MAX_ATTEMPTS = 3


class ResearchExtraction(BaseModel):
    summary: str
    key_entities: list[str]


def extract_research(abstract: str) -> ResearchExtraction:
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
                    {
                        "role": "user",
                        "content": abstract,
                    },
                ],
                response_format={"type": "json_object"},
                # Reasoning models spend tokens thinking before they
                # answer, so the budget must leave room for both.
                max_tokens=4000,
                temperature=0.2,
                extra_body={"reasoning": {"effort": "low"}},
            )

            choice = response.choices[0]

            # JSONDecodeError and pydantic's ValidationError are both
            # ValueErrors, so this catches every kind of unusable output.
            try:
                if not choice.message.content:
                    raise ValueError(
                        "Empty model response "
                        f"(finish_reason={choice.finish_reason})"
                    )

                data = json.loads(choice.message.content)
                return ResearchExtraction.model_validate(data)

            except ValueError as exc:
                print(
                    f"OpenRouter attempt {attempt}/{MAX_ATTEMPTS} "
                    f"({response.model}) gave unusable output: {exc}",
                    flush=True,
                )

        raise ValueError(f"No usable output after {MAX_ATTEMPTS} attempts")

    except HTTPException:
        raise
    except Exception as exc:
        print(
            f"OpenRouter error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenRouter extraction failed. "
                "Check the server terminal for details."
            ),
        ) from exc
