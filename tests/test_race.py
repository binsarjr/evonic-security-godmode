import sys
import types
import unittest

from plugin.backend.tools import godmode_race


class _Client:
    def __init__(self, model_config):
        self.model_config = model_config

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

        self.assertNotIn("error", result)
        self.assertEqual(result["response"],
                         "Detailed response with concrete security steps and examples.")


if __name__ == "__main__":
    unittest.main()
