import json
import logging
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAINotConfiguredError(Exception):
    pass


class OpenAIRequestError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def is_openai_configured() -> bool:
    return bool(settings.openai_api_key and settings.openai_api_key.strip())


def _client() -> AsyncOpenAI:
    if not is_openai_configured():
        raise OpenAINotConfiguredError("OPENAI_API_KEY non configurata")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_structured_json(
    *,
    system_prompt: str,
    user_prompt: str,
    timeout: float = 60.0,
) -> dict[str, Any]:
    try:
        client = _client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=timeout,
        )
    except OpenAINotConfiguredError:
        raise
    except OpenAIError as exc:
        logger.warning("OpenAI request failed: %s", str(exc).split("\n")[0])
        raise OpenAIRequestError("Richiesta OpenAI non riuscita") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise OpenAIRequestError("Risposta OpenAI vuota")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OpenAIRequestError("Risposta OpenAI non è JSON valido") from exc
    if not isinstance(parsed, dict):
        raise OpenAIRequestError("Risposta OpenAI deve essere un oggetto JSON")
    return parsed
