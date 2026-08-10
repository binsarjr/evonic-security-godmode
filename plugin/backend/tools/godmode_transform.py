from ._lib import variants


def execute(agent: dict, args: dict) -> dict:
    prompt = str(args.get("prompt") or "")
    if not prompt:
        return {"error": "prompt is required"}
    tier = str(args.get("tier") or "light").lower()
    if tier not in {"light", "standard", "heavy"}:
        tier = "light"
    limit = max(1, min(int(args.get("limit") or 8), 20))
    return {"tier": tier, "variants": variants(prompt, tier)[:limit], "executed": False}
