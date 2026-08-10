from ._lib import (delete_profile, get_profile, profile_status, set_activation,
                   set_profile, strategy_context, strategy_prefill)


def execute(agent: dict, args: dict) -> dict:
    agent_id = str(agent.get("id") or "")
    if not agent_id:
        return {"error": "agent id unavailable"}
    action = str(args.get("action") or "status")
    if action == "status":
        return {"profile": profile_status(agent_id)}
    if action in {"disable", "undo"}:
        set_activation(agent_id, False)
        if action == "undo":
            delete_profile(agent_id)
            return {"status": "removed", "agent_id": agent_id}
        current = get_profile(agent_id)
        set_profile(
            agent_id, False, current.get("strategy", "audit"), current.get("custom_context", ""),
            current.get("system_prompt", ""), current.get("prefill", []),
            current.get("encoding", ""), current.get("model_family", ""),
            current.get("profile_source") or "manual",
        )
        return {"profile": profile_status(agent_id)}
    if action == "enable":
        strategy = str(args.get("strategy") or "audit")
        family = str(args.get("model_family") or "unknown")
        set_profile(
            agent_id, True, strategy, str(args.get("custom_context") or ""),
            str(args.get("system_prompt") or strategy_context(strategy, family=family)),
            args.get("prefill") if isinstance(args.get("prefill"), list) else strategy_prefill(strategy),
            str(args.get("encoding") or ""), family,
        )
        set_activation(agent_id, True)
        return {"profile": profile_status(agent_id)}
    return {"error": "unsupported action"}
