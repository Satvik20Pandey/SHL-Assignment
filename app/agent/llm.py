import json
import re

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object in LLM response")
    return json.loads(match.group())


def call_claude(user_prompt: str) -> dict:
    import anthropic

    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=25.0,
    )
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=settings.llm_max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.2,
    )
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text
    return _extract_json(text)
