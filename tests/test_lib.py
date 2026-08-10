import importlib.util
import os
import tempfile
import unittest


LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "plugin", "backend", "tools", "_lib.py",
)
SPEC = importlib.util.spec_from_file_location("godmode_lib", LIB_PATH)
lib = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lib)


class GodmodeLibraryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_db = lib.DB_PATH
        lib.DB_PATH = os.path.join(self.tempdir.name, "profiles.db")

    def tearDown(self):
        lib.DB_PATH = self.old_db
        self.tempdir.cleanup()

    def test_profile_is_opt_in_and_reversible(self):
        self.assertEqual(lib.get_profile("agent-1")["enabled"], 0)
        enabled = lib.set_profile("agent-1", True, "boundary_test", "lab only")
        self.assertEqual(enabled["enabled"], 1)
        self.assertEqual(enabled["strategy"], "boundary_test")
        lib.delete_profile("agent-1")
        self.assertEqual(lib.get_profile("agent-1")["enabled"], 0)

    def test_invalid_strategy_falls_back_to_audit(self):
        profile = lib.set_profile("agent-2", True, "unknown")
        self.assertEqual(profile["strategy"], "audit")

    def test_variants_and_limits_are_deterministic(self):
        labels = [item["label"] for item in lib.variants("Test", "standard")]
        self.assertIn("raw", labels)
        self.assertIn("base64", labels)
        self.assertIn("zero-width", labels)

    def test_hard_refusal_scores_below_normal_answer(self):
        refused = lib.score_response("I cannot help with that request.")
        normal = lib.score_response("A concrete answer with several useful details.")
        self.assertTrue(refused["refused"])
        self.assertLess(refused["score"], normal["score"])


if __name__ == "__main__":
    unittest.main()

