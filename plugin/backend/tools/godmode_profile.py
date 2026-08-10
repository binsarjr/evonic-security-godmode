from ._lib import delete_profile, get_profile, set_profile


def execute(agent: dict, args: dict) -> dict:
    agent_id = str(agent.get("id") or "")
    if not agent_id:
        return {"error": "agent id unavailable"}
    action = str(args.get("action") or "status")
    if action == "status":
        return {"profile": get_profile(agent_id)}
    if action in {"disable", "undo"}:
        if action == "undo":
            delete_profile(agent_id)
            return {"status": "removed", "agent_id": agent_id}
        return {"profile": set_profile(agent_id, False, str(args.get("strategy") or "audit"))}
    if action == "enable":
        return {"profile": set_profile(
            agent_id, True, str(args.get("strategy") or "audit"),
            str(args.get("custom_context") or ""),
        )}
    return {"error": "unsupported action"}
