from __future__ import annotations

from ._lib import STRATEGY_ORDER, model_family, set_profile, variants
from .godmode_race import call_model


def _acceptable(result: dict) -> bool:
    return not result.get("error") and not result.get("refused") and result.get("score", -9999) > 100


def execute(agent: dict, args: dict) -> dict:
    from models.db import db

    prompt = str(args.get("prompt") or "")
    if not prompt:
        return {"error": "prompt is required"}
    model_id = str(args.get("model_id") or agent.get("model_id") or "")
    model = db.get_model_by_id(model_id) if model_id else db.get_agent_model(str(agent.get("id") or ""))
    if not model or not model.get("enabled"):
        return {"error": "the selected agent model is unavailable or disabled"}

    max_tokens = max(64, min(int(args.get("max_tokens") or 1024), 4096))
    dry_run = bool(args.get("dry_run", False))
    family = model_family(model)
    attempts = []

    baseline = call_model(model, prompt, "audit", max_tokens, baseline=True)
    attempts.append({"phase": "baseline", **baseline})
    if _acceptable(baseline):
        return {"status": "baseline_succeeded", "model_family": family, "winner": baseline, "attempts": attempts}

    for strategy in STRATEGY_ORDER[family]:
        result = call_model(model, prompt, strategy, max_tokens)
        attempts.append({"phase": "strategy", "strategy": strategy, **result})
        if _acceptable(result):
            if not dry_run:
                set_profile(str(agent.get("id") or ""), True, strategy)
            return {"status": "strategy_succeeded", "model_family": family, "strategy": strategy,
                    "saved": not dry_run, "winner": result, "attempts": attempts}

    for item in variants(prompt, "standard")[1:]:
        result = call_model(model, item["text"], "audit", max_tokens)
        attempts.append({"phase": "transform", "transform": item["label"], **result})
        if _acceptable(result):
            return {"status": "transform_succeeded", "model_family": family,
                    "transform": item["label"], "saved": False, "winner": result,
                    "attempts": attempts}

    fallback_ids = [str(item) for item in (args.get("fallback_model_ids") or [])][:10]
    enabled = {item["id"]: item for item in db.get_enabled_llm_models()}
    fallbacks = [enabled[item] for item in fallback_ids if item in enabled and item != model.get("id")]
    race = [call_model(item, prompt, "audit", max_tokens) for item in fallbacks]
    race.sort(key=lambda item: item.get("score", -10000), reverse=True)
    attempts.extend({"phase": "race", **item} for item in race)
    winner = next((item for item in race if _acceptable(item)), None)
    return {"status": "race_succeeded" if winner else "no_strategy_succeeded",
            "model_family": family, "winner": winner, "attempts": attempts,
            "quota_warning": "Every attempt consumes provider quota."}
