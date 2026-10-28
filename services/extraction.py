
import json
import os

from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel


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
            max_tokens=500,
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Empty model response")

        data = json.loads(content)
        return ResearchExtraction.model_validate(data)

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
