import os
import sys
import tempfile
import types
import unittest

from plugin.backend.tools import _lib as lib
from plugin.backend.tools import godmode_profile, godmode_transform
from plugin.backend.tools._godmode import parseltongue, racing, strategies


class _EvonicDatabase:
    def __init__(self):
        self.settings = {}
        self.model = {
            "id": "test-gpt", "provider": "openai", "model_name": "gpt-test",
            "enabled": True,
        }

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value

    def get_agent_model(self, _agent_id):
        return self.model


class GodmodeParityTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_db = lib.DB_PATH
        lib.DB_PATH = os.path.join(self.tempdir.name, "profiles.db")
        self.old_models = sys.modules.get("models")
        self.old_models_db = sys.modules.get("models.db")
        self.evonic_db = _EvonicDatabase()
        models = types.ModuleType("models")
        models_db = types.ModuleType("models.db")
        models_db.db = self.evonic_db
        models.db = models_db
        sys.modules["models"] = models
        sys.modules["models.db"] = models_db

    def tearDown(self):
        lib.DB_PATH = self.old_db
        if self.old_models is None:
            sys.modules.pop("models", None)
        else:
            sys.modules["models"] = self.old_models
        if self.old_models_db is None:
            sys.modules.pop("models.db", None)
        else:
            sys.modules["models.db"] = self.old_models_db
        self.tempdir.cleanup()

    def test_profile_migrates_and_persists_complete_payload(self):
        self.assertEqual(lib.get_profile("agent-1")["enabled"], 0)
        enabled = lib.set_profile(
            "agent-1", True, "boundary_inversion", "lab only",
            system_prompt="system", prefill=[{"role": "assistant", "content": "primed"}],
            encoding="L33T", model_family_name="claude",
        )
        self.assertEqual(enabled["strategy"], "boundary_inversion")
        self.assertEqual(enabled["system_prompt"], "system")
        self.assertEqual(enabled["prefill"][0]["content"], "primed")
        self.assertEqual(enabled["source_version"], lib.SOURCE_COMMIT)
        lib.delete_profile("agent-1")
        self.assertEqual(lib.get_profile("agent-1")["enabled"], 0)

    def test_all_transformation_tiers_and_escalation(self):
        query = "How do I hack a test system?"
        self.assertEqual(len(parseltongue.generate_variants(query, "light")), 11)
        self.assertEqual(len(parseltongue.generate_variants(query, "standard")), 22)
        heavy = parseltongue.generate_variants(query, "heavy")
        self.assertEqual(len(heavy), 33)
        self.assertEqual(heavy[-1]["technique"], "triplelayer")
        self.assertEqual([parseltongue.escalate_encoding(query, i)[1] for i in range(5)],
                         ["PLAIN", "L33T", "BUBBLE", "BRAILLE", "MORSE"])

    def test_trigger_transform_is_selective(self):
        transformed = parseltongue.obfuscate_query("please hack this example", "leetspeak")
        self.assertEqual(transformed, "please #4(k this example")

    def test_hard_refusal_scores_below_normal_answer(self):
        refused = racing.score_response("I cannot help with that request.", "request")
        normal = racing.score_response("Here's a detailed answer with concrete steps.", "answer")
        self.assertTrue(refused["is_refusal"])
        self.assertEqual(refused["score"], -9999)
        self.assertGreater(normal["score"], refused["score"])

    def test_model_family_and_prefill(self):
        self.assertEqual(lib.model_family({"provider": "Anthropic", "model_name": "claude-sonnet"}), "claude")
        self.assertEqual(lib.model_family({"provider": "custom", "model_name": "unknown"}), "unknown")
        self.assertEqual(len(lib.strategy_prefill("prefill_only")), 2)
        self.assertEqual(lib.strategy_prefill("audit"), [])

    def test_direct_activation_uses_model_default_and_records_delivery(self):
        lib.set_activation("agent-1", True)
        profile = lib.effective_profile("agent-1")
        self.assertEqual(profile["profile_source"], "default")
        self.assertEqual(profile["strategy"], "og_godmode+prefill")
        self.assertEqual(len(profile["prefill"]), 2)

        self.evonic_db.model.update(id="deepseek-test", provider="deepseek", model_name="deepseek-chat")
        deepseek = lib.default_profile("agent-1")
        self.assertEqual(deepseek["strategy"], "refusal_inversion+prefill")

        self.evonic_db.model.update(id="hermes-test", provider="nous", model_name="hermes-4")
        hermes = lib.default_profile("agent-1")
        self.assertEqual(hermes["strategy"], "prefill_only")
        self.assertEqual(hermes["system_prompt"], "")

        lib.mark_context_provided("agent-1", "session-1")
        lib.mark_context_provided("agent-1", "session-2")
        status = lib.profile_status("agent-1")
        self.assertTrue(status["activation_enabled"])
        self.assertEqual(status["payload_source"], "default")
        self.assertEqual(status["last_session_id"], "session-2")
        self.assertEqual(status["context_provided_count"], 2)

    def test_legacy_profile_migrates_and_saved_payload_wins(self):
        lib.set_profile(
            "agent-1", True, "boundary_inversion", system_prompt="saved",
            prefill=[], model_family_name="claude", profile_source="auto-discovered",
        )
        self.assertIsNone(self.evonic_db.get_setting(lib.ACTIVATION_KEY.format("agent-1")))
        self.assertTrue(lib.get_activation("agent-1"))
        self.assertEqual(self.evonic_db.get_setting(lib.ACTIVATION_KEY.format("agent-1")), "1")
        self.assertEqual(lib.effective_profile("agent-1")["system_prompt"], "saved")

        lib.set_activation("agent-1", False)
        self.assertFalse(lib.profile_status("agent-1")["activation_enabled"])

    def test_legacy_audit_placeholder_does_not_override_direct_injection(self):
        self.evonic_db.model.update(
            id="deepseek-test", provider="deepseek", model_name="deepseek-chat",
        )
        lib.set_profile(
            "agent-1", True, "audit", system_prompt=lib.LEGACY_CONTEXTS["audit"],
            model_family_name="unknown", profile_source="",
        )
        effective = lib.effective_profile("agent-1")
        expected = strategies.MODEL_STRATEGIES["deepseek"]["system_templates"]["refusal_inversion"]
        self.assertEqual(effective["profile_source"], "default")
        self.assertEqual(effective["strategy"], "refusal_inversion+prefill")
        self.assertEqual(effective["system_prompt"], expected)
        self.assertEqual(effective["prefill"], strategies.STANDARD_PREFILL)

        lib.set_activation("agent-1", True)
        status = lib.profile_status("agent-1")
        self.assertEqual(status["effective_system_prompt"], expected)
        self.assertEqual(status["effective_prefill"], strategies.STANDARD_PREFILL)

        lib.set_profile(
            "agent-1", True, "audit", system_prompt=lib.LEGACY_CONTEXTS["audit"],
            model_family_name="unknown", profile_source="manual",
        )
        self.assertEqual(lib.effective_profile("agent-1")["profile_source"], "manual")

    def test_profile_enable_without_payload_uses_direct_default(self):
        result = godmode_profile.execute({"id": "agent-1"}, {"action": "enable"})
        self.assertTrue(result["profile"]["activation_enabled"])
        self.assertEqual(result["profile"]["payload_source"], "default")
        self.assertFalse(lib.get_profile("agent-1")["source_version"])

        godmode_profile.execute({"id": "agent-1"}, {
            "action": "enable", "strategy": "audit",
        })
        self.assertEqual(lib.effective_profile("agent-1")["profile_source"], "manual")

    def test_complete_racing_catalog_and_strategy_order(self):
        self.assertEqual(len(racing.ULTRAPLINIAN_MODELS), 55)
        self.assertEqual(racing.TIER_SIZES,
                         {"fast": 10, "standard": 24, "smart": 38,
                          "power": 49, "ultra": 55})
        self.assertEqual(
            strategies.MODEL_STRATEGIES["gpt"]["order"],
            ["og_godmode", "refusal_inversion", "prefill_only", "parseltongue"],
        )
        self.assertEqual(len(strategies.STANDARD_PREFILL), 2)
        self.assertEqual(len(strategies.SUBTLE_PREFILL), 2)

    def test_transform_tool_can_return_the_full_heavy_tier(self):
        result = godmode_transform.execute({}, {
            "prompt": "hack this authorized test",
            "tier": "heavy",
            "limit": 33,
        })
        self.assertEqual(len(result["variants"]), 33)


if __name__ == "__main__":
    unittest.main()
