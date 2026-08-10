import os
import tempfile
import unittest

from plugin.backend.tools import _lib as lib
from plugin.backend.tools import godmode_transform
from plugin.backend.tools._godmode import parseltongue, racing, strategies


class GodmodeParityTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_db = lib.DB_PATH
        lib.DB_PATH = os.path.join(self.tempdir.name, "profiles.db")

    def tearDown(self):
        lib.DB_PATH = self.old_db
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
