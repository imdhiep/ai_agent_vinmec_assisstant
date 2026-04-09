from __future__ import annotations

from pathlib import Path
from typing import Any

from openai import OpenAI

from app.config import SYSTEM_PROMPT_FILE


DEFAULT_BASE_URL = "https://models.github.ai/inference"
DEFAULT_MODEL = "openai/gpt-4o"


def load_system_prompt() -> str:
    return Path(SYSTEM_PROMPT_FILE).read_text(encoding="utf-8")


def build_client(api_key: str | None, base_url: str | None = None) -> OpenAI | None:
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url=base_url or DEFAULT_BASE_URL,
    )


def ask_booking_agent(
    client: OpenAI | None,
    user_message: str,
    catalog_context: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> str | None:
    if client is None:
        return None

    system_prompt = load_system_prompt()
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Dữ liệu catalog đặt khám hiện tại:\n"
                    f"{catalog_context}\n\n"
                    "Yêu cầu của bệnh nhân:\n"
                    f"{user_message}"
                ),
            },
        ],
    )
    return response.choices[0].message.content if response.choices else None
