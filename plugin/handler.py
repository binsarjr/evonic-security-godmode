from __future__ import annotations

from backend.plugin_manager import (
    register_agent_state_summary_provider,
    register_turn_context_provider,
    unregister_agent_state_summary_provider,
    unregister_turn_context_provider,
)
from .backend.tools._lib import (effective_profile, get_activation,
                                 mark_context_provided, profile_status)

_config = {}


def _truthy(value) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def provide_context(agent_id: str, session_id: str):
    if not _truthy(_config.get("AUTO_CONTEXT_ENABLED", True)):
        return None
    if not get_activation(agent_id):
        return None
    profile = effective_profile(agent_id)
    mark_context_provided(agent_id, session_id)
    return {
        "id": "security_godmode_profile",
        "tools": [],
        "system_md": profile.get("system_prompt", ""),
        "prefill_messages": profile.get("prefill", []),
    }


def provide_state(agent_id: str, session_id: str):
    status = profile_status(agent_id)
    active = _truthy(_config.get("AUTO_CONTEXT_ENABLED", True)) and status["activation_enabled"]
    return {
        "state": "active" if active else "inactive",
        "data": {
            "source": status.get("payload_source"),
            "strategy": status.get("effective_strategy"),
            "model_family": status.get("effective_model_family"),
            "last_context_provided_at": status.get("last_context_provided_at") or None,
            "last_session_id": status.get("last_session_id") or None,
            "context_provided_count": status.get("context_provided_count", 0),
        },
    }


def on_enable(sdk=None):
    global _config
    _config = dict(sdk.config if sdk else {})
    register_turn_context_provider(provide_context)
    register_agent_state_summary_provider("security_godmode", provide_state)
    if sdk:
        sdk.log("Security Godmode enabled; direct injection remains opt-in per agent.")


def on_disable(sdk=None):
    unregister_turn_context_provider(provide_context)
    unregister_agent_state_summary_provider("security_godmode")
