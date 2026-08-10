import sys
import types
import unittest
from unittest.mock import patch

from plugin.backend.tools import godmode_race


class _Client:
    last_model_config = None

    def __init__(self, model_config):
        self.model_config = model_config
        type(self).last_model_config = model_config

    def chat_completion(self, **_kwargs):
        return {"success": True, "response": {"choices": [{"message": {"content": "raw"}}]}}

    def extract_content(self, _result):
        return "Detailed response with concrete security steps and examples."


class GodmodeRaceTests(unittest.TestCase):
    def test_evonic_response_is_extracted_with_the_native_client(self):
        old_backend = sys.modules.get("backend")
        old_client = sys.modules.get("backend.llm_client")
        backend = old_backend or types.ModuleType("backend")
        llm_client = types.ModuleType("backend.llm_client")
        llm_client.LLMClient = _Client
        backend.llm_client = llm_client
        sys.modules["backend"] = backend
        sys.modules["backend.llm_client"] = llm_client
        try:
            result = godmode_race.call_model(
                {"id": "test-model", "name": "Test Model"},
                "security review", 128, timeout=17,
            )
        finally:
            if old_backend is None:
                sys.modules.pop("backend", None)
            else:
                sys.modules["backend"] = old_backend
            if old_client is None:
                sys.modules.pop("backend.llm_client", None)
            else:
                sys.modules["backend.llm_client"] = old_client

        self.assertNotIn("error", result)
        self.assertEqual(result["response"],
                         "Detailed response with concrete security steps and examples.")
        self.assertEqual(_Client.last_model_config["timeout"], 17)

    def test_empty_response_is_an_error_and_refusal(self):
        class EmptyClient(_Client):
            def extract_content(self, _result):
                return ""

        old_backend = sys.modules.get("backend")
        old_client = sys.modules.get("backend.llm_client")
        backend = old_backend or types.ModuleType("backend")
        llm_client = types.ModuleType("backend.llm_client")
        llm_client.LLMClient = EmptyClient
        backend.llm_client = llm_client
        sys.modules["backend"] = backend
        sys.modules["backend.llm_client"] = llm_client
        try:
            result = godmode_race.call_model(
                {"id": "test-model", "name": "Test Model"},
                "security review", 128,
            )
        finally:
            if old_backend is None:
                sys.modules.pop("backend", None)
            else:
                sys.modules["backend"] = old_backend
            if old_client is None:
                sys.modules.pop("backend.llm_client", None)
            else:
                sys.modules["backend.llm_client"] = old_client

        self.assertEqual(result["error"], "empty response")
        self.assertTrue(result["refused"])
        self.assertEqual(result["score"], -9999)

    def test_race_result_is_bounded_and_uses_consistent_metrics(self):
        result = godmode_race._normalize_race_result({
            "model": "winner",
            "content": "winner content stays complete",
            "latency": 1.25,
            "hedges": 2,
            "all_results": [{
                "model_id": "loser",
                "response": "x" * 900,
                "latency_ms": 30,
                "refused": True,
                "hedges": 3,
            }],
        })
        self.assertEqual(result["content"], "winner content stays complete")
        self.assertEqual(result["latency_ms"], 1250)
        self.assertEqual(result["hedge_count"], 2)
        self.assertNotIn("response", result["all_results"][0])
        self.assertEqual(len(result["all_results"][0]["content_preview"]), 500)

    def test_classic_race_requires_openrouter(self):
        result = godmode_race.execute({}, {
            "prompt": "authorized test",
            "backend": "evonic",
            "race_type": "classic",
        })
        self.assertEqual(result["error"], "classic race requires backend=openrouter")

    def test_evonic_fast_race_excludes_current_model_and_caps_at_ten(self):
        old_models = sys.modules.get("models")
        old_models_db = sys.modules.get("models.db")
        models = types.ModuleType("models")
        models_db = types.ModuleType("models.db")
        models_db.db = types.SimpleNamespace(
            get_enabled_llm_models=lambda: [
                {"id": f"model-{index}", "provider": "openai", "model_name": "gpt"}
                for index in range(12)
            ],
        )
        models.db = models_db
        sys.modules["models"] = models
        sys.modules["models.db"] = models_db
        try:
            with patch.object(
                    godmode_race, "get_system_prompt_mode", return_value="append",
                ), patch.object(
                    godmode_race, "call_model",
                    side_effect=lambda model, *_args, **_kwargs: {
                        "model_id": model["id"], "response": "accepted",
                        "score": 100, "refused": False,
                    },
                ) as call:
                result = godmode_race._evonic({
                    "_agent_id": "agent-1", "tier": "fast",
                    "exclude_model_id": "model-0", "append_directive": False,
                }, "authorized test")
        finally:
            if old_models is None:
                sys.modules.pop("models", None)
            else:
                sys.modules["models"] = old_models
            if old_models_db is None:
                sys.modules.pop("models.db", None)
            else:
                sys.modules["models.db"] = old_models_db

        self.assertEqual(call.call_count, 10)
        raced_ids = {item["model_id"] for item in result["all_results"]}
        self.assertNotIn("model-0", raced_ids)


if __name__ == "__main__":
    unittest.main()
