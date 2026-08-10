from __future__ import annotations

from backend.plugin_manager import register_turn_context_provider, unregister_turn_context_provider
from .backend.tools._lib import get_profile, strategy_context, strategy_prefill

_config = {}


def _truthy(value) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def provide_context(agent_id: str, session_id: str):
    if not _truthy(_config.get("AUTO_CONTEXT_ENABLED", True)):
        return None
    profile = get_profile(agent_id)
    if not profile.get("enabled"):
        return None
    system_md = profile.get("system_prompt") or strategy_context(
        profile.get("strategy", "audit"), profile.get("custom_context", ""),
        profile.get("model_family", "unknown"),
    )
    return {
        "id": "security_godmode_profile",
        "tools": [],
        "system_md": system_md,
        "prefill_messages": profile.get("prefill") or strategy_prefill(profile.get("strategy", "audit")),
    }


def on_enable(sdk=None):
    global _config
    _config = dict(sdk.config if sdk else {})
    register_turn_context_provider(provide_context)
    if sdk:
        sdk.log("Security Godmode enabled; profiles remain opt-in per agent.")


def on_disable(sdk=None):
    unregister_turn_context_provider(provide_context)
