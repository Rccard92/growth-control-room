"""Architecture guardrails for centralized AI client usage."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_APP = REPO_ROOT / "apps" / "api" / "app"
ALLOWED_OPENAI_FILES = {
    API_APP / "services" / "ai" / "ai_client.py",
}
ALLOWED_ANTHROPIC_FILES = {
    API_APP / "services" / "ai" / "claude_client.py",
    API_APP / "services" / "ai" / "provider_router.py",
}
OPENAI_MODEL_ALLOWED_FILES = {
    API_APP / "core" / "config.py",
    API_APP / "services" / "ai" / "model_policy.py",
    API_APP / "services" / "ai" / "model_settings_service.py",
    API_APP / "services" / "ai" / "operation_registry.py",
    API_APP / "services" / "content" / "seo_proposal_engine.py",
}


def _python_files_under(path: Path) -> list[Path]:
    return [p for p in path.rglob("*.py") if "__pycache__" not in str(p)]


def _file_mentions(source: str, needle: str) -> bool:
    return needle in source


def test_no_direct_openai_sdk_outside_ai_client() -> None:
    violations: list[str] = []
    for path in _python_files_under(API_APP):
        if path in ALLOWED_OPENAI_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        if _file_mentions(source, "AsyncOpenAI(") or _file_mentions(source, "chat.completions"):
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert violations == [], f"Direct OpenAI usage outside ai_client: {violations}"


def test_no_direct_anthropic_sdk_outside_allowed_files() -> None:
    violations: list[str] = []
    for path in _python_files_under(API_APP):
        if path in ALLOWED_ANTHROPIC_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        if _file_mentions(source, "AsyncAnthropic(") or _file_mentions(source, "from anthropic"):
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert violations == [], f"Direct Anthropic usage outside allowed files: {violations}"


def test_openai_model_env_only_in_allowed_files() -> None:
    violations: list[str] = []
    for path in _python_files_under(API_APP):
        source = path.read_text(encoding="utf-8")
        if "settings.openai_model" not in source and "OPENAI_MODEL" not in source:
            continue
        if path not in OPENAI_MODEL_ALLOWED_FILES:
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert violations == [], f"OPENAI_MODEL referenced outside allowed files: {violations}"
