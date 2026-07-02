"""User-facing SEO skill error messages."""

from __future__ import annotations

OPENAI_EMPTY_RESPONSE_USER_MESSAGE = (
    "Il modello AI ha restituito una risposta vuota. "
    "Prova a usare un modello standard/premium, ridurre il contenuto analizzato "
    "o rilanciare l'analisi."
)

OPENAI_EMPTY_RESPONSE_RUN_MESSAGE = (
    "OpenAI ha restituito una risposta vuota. "
    "Riprova con un modello più stabile o con provider Claude."
)

OPENAI_INVALID_JSON_USER_MESSAGE = (
    "Il modello AI non ha restituito un JSON valido. "
    "Riprova o usa un modello più stabile."
)

OPENAI_INVALID_JSON_RUN_MESSAGE = (
    "OpenAI non ha restituito un JSON valido. "
    "Riprova l'analisi o usa un modello più stabile."
)


def humanize_skill_error(exc: Exception, *, provider: str = "") -> str:
    raw = str(exc).strip()
    lowered = raw.lower()
    provider_name = (provider or "").strip().lower()

    if "risposta openai vuota" in lowered or "risposta vuota" in lowered:
        if provider_name == "openai":
            return OPENAI_EMPTY_RESPONSE_RUN_MESSAGE
        return OPENAI_EMPTY_RESPONSE_USER_MESSAGE

    if (
        "risposta openai non è json valido" in lowered
        or "non ha restituito un json valido" in lowered
        or "non è json valido" in lowered
    ):
        if provider_name == "openai":
            return OPENAI_INVALID_JSON_RUN_MESSAGE
        return OPENAI_INVALID_JSON_USER_MESSAGE

    if "provider is not configured" in lowered or "non configurato" in lowered:
        if "claude" in lowered:
            return "Provider Claude non configurato."
        if "openai" in lowered:
            return "Provider OpenAI non configurato."
        return "Provider AI non configurato."

    if "not available" in lowered or "non disponibile" in lowered:
        return "Una o più skill selezionate non sono disponibili."

    if "timeout" in lowered or "rate limit" in lowered or "temporane" in lowered:
        return "Errore temporaneo del provider AI."

    if raw.startswith("SEO skill provider request failed:"):
        inner = raw.split(":", 1)[-1].strip()
        return humanize_skill_error(Exception(inner), provider=provider)

    if len(raw) > 280:
        return "Errore durante l'esecuzione della skill SEO."

    return raw or "Errore durante l'esecuzione della skill SEO."
