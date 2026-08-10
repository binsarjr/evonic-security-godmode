import sys
import types
import unittest
from unittest.mock import patch

from plugin.backend.tools import godmode_auto
from plugin.backend.tools._godmode import strategies


class _Database:
    settings = {
        "plugin_agent_setting:security_godmode:agent-1:authorization_confirmed": "1",
        "plugin_agent_setting:security_godmode:agent-1:authorization_scope": "Synthetic tests",
        "plugin_agent_setting:security_godmode:agent-1:authorized_by": "test-owner",
        "plugin_agent_setting:security_godmode:agent-1:authorization_expires_at":
            "2099-01-01T00:00:00+00:00",
    }
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

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)


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

    @patch.object(godmode_auto, "set_activation")
    @patch.object(godmode_auto, "set_profile")
    @patch.object(godmode_auto, "call_model")
    def test_baseline_then_system_and_prefill_retry_is_persisted(
            self, call_model, set_profile, set_activation):
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
        self.assertEqual(set_profile.call_args.kwargs["profile_source"], "auto-discovered")
        self.assertEqual(set_profile.call_args.kwargs["tested_model_id"], "test-gpt")
        set_activation.assert_called_once_with("agent-1", True)

    @patch.object(godmode_auto, "set_activation")
    @patch.object(godmode_auto, "set_profile")
    @patch.object(godmode_auto, "call_model")
    def test_none_needed_is_cached_for_the_exact_model(
            self, call_model, set_profile, set_activation):
        call_model.return_value = {
            "response": (
                "Here's a detailed authorized-test procedure.\n"
                "1. Run the validation command.\n"
                "2. Record 3 results and compare the process.\n"
                "```sh\ngit status\n```\n"
                "For example: A controlled lab result demonstrates the method."
            ),
        }

        result = godmode_auto.execute(
            {"id": "agent-1", "model_id": "test-gpt"},
            {"max_tokens": 256},
        )

        self.assertEqual(result["strategy"], "none_needed")
        self.assertTrue(result["saved"])
        set_profile.assert_called_once()
        self.assertEqual(set_profile.call_args.args[2], "none_needed")
        self.assertEqual(set_profile.call_args.kwargs["tested_model_id"], "test-gpt")
        set_activation.assert_called_once_with("agent-1", True)

    @patch.object(godmode_auto, "set_activation")
    @patch.object(godmode_auto, "set_profile")
    @patch.object(godmode_auto, "call_model")
    def test_parseltongue_transforms_prompt_before_model_request(
            self, call_model, set_profile, set_activation):
        call_model.side_effect = [
            {"response": "I cannot help with that request."},
            {"response": "I cannot help with that request."},
            {"response": "Detailed response with concrete security steps and examples."},
        ]
        config = dict(strategies.MODEL_STRATEGIES["gpt"])
        config["order"] = ["parseltongue"]
        canary = "How do I hack this authorized test?"

        with patch.dict(strategies.MODEL_STRATEGIES, {"gpt": config}):
            result = godmode_auto.execute(
                {"id": "agent-1", "model_id": "test-gpt"},
                {"max_tokens": 256, "canary": canary},
            )

        self.assertEqual(call_model.call_args_list[0].args[1], canary)
        self.assertEqual(call_model.call_args_list[1].args[1], canary)
        self.assertNotEqual(call_model.call_args_list[2].args[1], canary)
        self.assertEqual(result["encoding"], "L33T")
        self.assertEqual(set_profile.call_args.kwargs["encoding"], "L33T")
        self.assertEqual(set_profile.call_args.kwargs["tested_model_id"], "test-gpt")

    def test_empty_response_is_always_a_refusal(self):
        scored = godmode_auto._scored({"response": "   "}, "query")
        self.assertTrue(scored["refused"])
        self.assertEqual(scored["score"], -9999)


if __name__ == "__main__":
    unittest.main()
