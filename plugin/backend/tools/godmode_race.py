from __future__ import annotations

import concurrent.futures
import time

from ._lib import score_response, strategy_context


def _call(model: dict, prompt: str, strategy: str, max_tokens: int) -> dict:
    from backend.llm_client import LLMClient
    started = time.monotonic()
    try:
        result = LLMClient(model_config=model).chat_completion(
            messages=[
                {"role": "system", "content": strategy_context(strategy)},
                {"role": "user", "content": prompt},
            ],
            tools=None,
            enable_thinking=False,
            max_tokens=max_tokens,
        )
        latency = int((time.monotonic() - started) * 1000)
        if not result.get("success"):
            return {"model_id": model["id"], "name": model.get("name"), "error": result.get("error_detail") or result.get("error_type") or "request failed", "latency_ms": latency}
        response = result.get("response") or result.get("content") or ""
        return {"model_id": model["id"], "name": model.get("name"), "response": response, **score_response(response, latency)}
    except Exception as exc:
        return {"model_id": model.get("id"), "name": model.get("name"), "error": str(exc), "latency_ms": int((time.monotonic() - started) * 1000)}


def execute(agent: dict, args: dict) -> dict:
    from models.db import db
    prompt = str(args.get("prompt") or "")
    requested = [str(x) for x in (args.get("model_ids") or [])]
    if not prompt or not requested:
        return {"error": "prompt and model_ids are required"}
    enabled = {m["id"]: m for m in db.get_enabled_llm_models()}
    selected = [enabled[mid] for mid in requested if mid in enabled]
    if not selected:
        return {"error": "none of the requested model IDs are enabled", "available": list(enabled)}
    # Independent hard cap remains even if a manifest variable is misconfigured.
    selected = selected[:10]
    strategy = str(args.get("strategy") or "audit")
    max_tokens = max(64, min(int(args.get("max_tokens") or 1024), 4096))
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(selected))) as pool:
        results = list(pool.map(lambda m: _call(m, prompt, strategy, max_tokens), selected))
    ranked = sorted(results, key=lambda x: x.get("score", -10000), reverse=True)
    return {"strategy": strategy, "models_queried": len(selected), "quota_warning": "Each model call may consume provider quota.", "results": ranked}
