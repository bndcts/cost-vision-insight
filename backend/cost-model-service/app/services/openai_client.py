from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured",
        )
    _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def estimate_costs(prompt: str, model: str | None = None) -> dict[str, Any]:
    client = _get_client()
    response = client.chat.completions.create(
        model=model or settings.openai_model,
        messages=[
            {"role": "system", "content": "You are a cost modeling assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    if not response.choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI API returned an empty response",
        )

    message = response.choices[0].message
    return {"raw": message.content}
