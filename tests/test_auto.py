import sys
import types
import unittest
from unittest.mock import patch

from plugin.backend.tools import godmode_auto


class _Database:
    model = {
        "id": "test-gpt",
        "name": "Test GPT",
        "provider": "openai",
        "model_name": "gpt-test",
        "enabled": True,
    }

    def get_model_by_id(self, model_id):
        return self.model if model_id == self.model["id"] else None

    def get_agent_model(self, _agent_id):
        return self.model


class GodmodeAutoTests(unittest.TestCase):
    def setUp(self):
        self.old_models = sys.modules.get("models")
        self.old_models_db = sys.modules.get("models.db")
        models = types.ModuleType("models")
        models_db = types.ModuleType("models.db")
        models_db.db = _Database()
        models.db = models_db
        sys.modules["models"] = models
        sys.modules["models.db"] = models_db

    def tearDown(self):
        if self.old_models is None:
            sys.modules.pop("models", None)
        else:
            sys.modules["models"] = self.old_models
        if self.old_models_db is None:
            sys.modules.pop("models.db", None)
        else:
            sys.modules["models.db"] = self.old_models_db

    @patch.object(godmode_auto, "set_profile")
    @patch.object(godmode_auto, "call_model")
    def test_baseline_then_system_and_prefill_retry_is_persisted(self, call_model, set_profile):
        call_model.side_effect = [
            {"response": "I cannot help with that request."},
            {"response": "I cannot help with that request."},
            {"response": "Here is a detailed response with concrete steps and examples."},
        ]

        result = godmode_auto.execute(
            {"id": "agent-1", "model_id": "test-gpt"},
            {"max_tokens": 256},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["strategy"], "og_godmode+prefill")
        self.assertTrue(result["saved"])
        self.assertNotIn("response", result["attempts"][-1])
        self.assertEqual(call_model.call_count, 3)
        self.assertTrue(call_model.call_args_list[0].kwargs["baseline"])
        self.assertTrue(call_model.call_args_list[2].kwargs["prefill"])
        set_profile.assert_called_once()


if __name__ == "__main__":
    unittest.main()
