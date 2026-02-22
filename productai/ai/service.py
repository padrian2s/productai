"""Claude AI service for streaming product management assistance."""

import os
import json
from collections.abc import AsyncGenerator
from anthropic import AsyncAnthropic
from .prompts import (
    PLAN_MODE_SYSTEM, PRD_GENERATION_SYSTEM, PRD_REFINE_SYSTEM,
    ENHANCE_LIGHT_SYSTEM, ENHANCE_MEDIUM_SYSTEM, ENHANCE_HEAVY_SYSTEM,
)
from ..db.models import get_setting


_cached_db_key: str | None = None
_cached_db_key_loaded = False


async def _get_api_key() -> str:
    """Return API key: env var wins, then DB setting."""
    env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key
    global _cached_db_key, _cached_db_key_loaded
    if not _cached_db_key_loaded:
        _cached_db_key = await get_setting("anthropic_api_key")
        _cached_db_key_loaded = True
    return _cached_db_key or ""


def invalidate_api_key_cache():
    """Call after updating the DB key so next request picks it up."""
    global _cached_db_key, _cached_db_key_loaded
    _cached_db_key = None
    _cached_db_key_loaded = False


def get_client_sync(api_key: str = "") -> AsyncAnthropic:
    return AsyncAnthropic(api_key=api_key)


async def get_client() -> AsyncAnthropic:
    key = await _get_api_key()
    return AsyncAnthropic(api_key=key)


async def stream_chat(
    system_prompt: str,
    messages: list[dict],
    model: str = "claude-sonnet-4-20250514",
) -> AsyncGenerator[str, None]:
    """Stream a Claude response token by token."""
    client = await get_client()
    async with client.messages.stream(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def generate_full(
    system_prompt: str,
    messages: list[dict],
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Get a complete Claude response (non-streaming)."""
    client = await get_client()
    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


async def stream_plan_chat(
    messages: list[dict],
) -> AsyncGenerator[str, None]:
    """Stream a plan-mode conversation response."""
    async for token in stream_chat(PLAN_MODE_SYSTEM, messages):
        yield token


async def stream_prd_generation(
    context: str,
) -> AsyncGenerator[str, None]:
    """Stream PRD generation from a product description/context."""
    messages = [
        {
            "role": "user",
            "content": f"Generate a comprehensive PRD based on the following context:\n\n{context}",
        }
    ]
    async for token in stream_chat(PRD_GENERATION_SYSTEM, messages):
        yield token


async def stream_prd_refinement(
    current_prd: str,
    instruction: str,
    messages: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream PRD refinement suggestions."""
    if messages is None:
        messages = []
    messages.append(
        {
            "role": "user",
            "content": f"Here is the current PRD:\n\n{current_prd}\n\nPlease help with: {instruction}",
        }
    )
    async for token in stream_chat(PRD_REFINE_SYSTEM, messages):
        yield token


ENHANCE_FALLBACKS = {
    "light": ENHANCE_LIGHT_SYSTEM,
    "medium": ENHANCE_MEDIUM_SYSTEM,
    "heavy": ENHANCE_HEAVY_SYSTEM,
}

ENHANCE_SETTING_KEYS = {
    "light": "enhance_light",
    "medium": "enhance_medium",
    "heavy": "enhance_heavy",
}


async def _get_enhance_prompt(intensity: str) -> str:
    """Load enhancement prompt from DB settings, falling back to hardcoded default."""
    key = ENHANCE_SETTING_KEYS.get(intensity, "enhance_medium")
    prompt = await get_setting(key)
    return prompt or ENHANCE_FALLBACKS.get(intensity, ENHANCE_MEDIUM_SYSTEM)


async def stream_enhance_field(
    text: str,
    field_label: str,
    intensity: str,
    instruction: str = "",
) -> AsyncGenerator[str, None]:
    """Stream an AI-enhanced version of a form field's text."""
    system = await _get_enhance_prompt(intensity)
    user_content = (
        f"The following is the \"{field_label}\" field of a product document. "
        f"Enhance it:\n\n{text}"
    )
    if instruction:
        user_content += f"\n\nAdditional instructions from the user: {instruction}"
    messages = [{"role": "user", "content": user_content}]
    async for token in stream_chat(system, messages):
        yield token


async def stream_enhance_selection(
    full_text: str,
    selected_text: str,
    field_label: str,
    intensity: str,
    instruction: str = "",
) -> AsyncGenerator[str, None]:
    """Stream an AI-enhanced version of a selected portion of text."""
    system = await _get_enhance_prompt(intensity)
    user_content = (
        f"The following is the full \"{field_label}\" field of a product document:\n\n"
        f"---\n{full_text}\n---\n\n"
        f"The user has SELECTED the following portion to enhance:\n\n"
        f">>> {selected_text} <<<\n\n"
        f"Enhance ONLY the selected portion. Return ONLY the replacement text for the selected portion, "
        f"nothing else. Keep it consistent with the surrounding context."
    )
    if instruction:
        user_content += f"\n\nAdditional instructions from the user: {instruction}"
    messages = [{"role": "user", "content": user_content}]
    async for token in stream_chat(system, messages):
        yield token


async def generate_plan_summary(plan_data: dict) -> AsyncGenerator[str, None]:
    """Generate a structured plan summary from collected data."""
    context = json.dumps(plan_data, indent=2)
    messages = [
        {
            "role": "user",
            "content": (
                "Based on our conversation, please generate a comprehensive product plan summary "
                f"from this data:\n\n{context}\n\n"
                "Format it as a well-structured document with clear sections."
            ),
        }
    ]
    async for token in stream_chat(PLAN_MODE_SYSTEM, messages):
        yield token
