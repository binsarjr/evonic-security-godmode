import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class HandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_backend = sys.modules.get("backend")
        cls.old_manager = sys.modules.get("backend.plugin_manager")
        backend = cls.old_backend or types.ModuleType("backend")
        manager = types.ModuleType("backend.plugin_manager")
        for name in (
            "apply_turn_context",
            "register_agent_state_summary_provider",
            "register_final_response_handler",
            "register_turn_context_provider",
            "register_user_message_transformer",
            "unregister_agent_state_summary_provider",
            "unregister_final_response_handler",
            "unregister_turn_context_provider",
            "unregister_user_message_transformer",
        ):
            setattr(manager, name, Mock())
        backend.plugin_manager = manager
        sys.modules["backend"] = backend
        sys.modules["backend.plugin_manager"] = manager
        cls.manager = manager
        cls.handler = importlib.import_module("plugin.handler")

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("plugin.handler", None)
        if cls.old_backend is None:
            sys.modules.pop("backend", None)
        else:
            sys.modules["backend"] = cls.old_backend
        if cls.old_manager is None:
            sys.modules.pop("backend.plugin_manager", None)
        else:
            sys.modules["backend.plugin_manager"] = cls.old_manager

    def test_enable_registers_direct_context_state_and_transform_hooks(self):
        sdk = types.SimpleNamespace(config={"AUTO_CONTEXT_ENABLED": True}, log=Mock())
        self.handler.on_enable(sdk)
        self.manager.register_turn_context_provider.assert_called_with(
            self.handler.provide_context
        )
        self.manager.register_user_message_transformer.assert_called_with(
            "security_godmode", self.handler.transform_user_message
        )
        self.manager.register_agent_state_summary_provider.assert_called_with(
            "security_godmode", self.handler.provide_state
        )
        self.manager.register_final_response_handler.assert_called_with(
            "security_godmode", self.handler.evaluate_final_response
        )

    def test_active_transform_happens_and_records_receipt(self):
        self.handler._config = {"AUTO_CONTEXT_ENABLED": True}
        with patch.object(self.handler, "get_activation", return_value=True), \
                patch.object(
                    self.handler, "authorization_status",
                    return_value={"authorization_valid": True},
                ), \
                patch.object(
                    self.handler, "transform_policy",
                    return_value={"mode": "forced", "encoding": "L33T", "forced": True},
                ), patch.object(
                    self.handler, "transform_text", return_value="#4(k request"
                ) as transform, patch.object(
                    self.handler, "mark_transform_applied"
                ) as receipt:
            result = self.handler.transform_user_message(
                "agent-1", "session-1", "hack request"
            )

        self.assertEqual(result, "#4(k request")
        transform.assert_called_once_with("hack request", "L33T")
        receipt.assert_called_once_with("agent-1", "session-1", "L33T", True)

    def test_invalid_authorization_blocks_context_and_transform(self):
        self.handler._config = {"AUTO_CONTEXT_ENABLED": True}
        with patch.object(self.handler, "get_activation", return_value=True), \
                patch.object(self.handler, "effective_profile", return_value={}), \
                patch.object(self.handler, "scoped_profile", return_value=None), \
                patch.object(
                    self.handler, "authorization_status",
                    return_value={"authorization_valid": False},
                ):
            self.assertIsNone(self.handler.provide_context("agent-1", "session-1"))
            self.assertEqual(
                self.handler.transform_user_message(
                    "agent-1", "session-1", "hack request"
                ),
                "hack request",
            )

    def test_context_maps_preserve_append_and_override_modes(self):
        self.handler._config = {"AUTO_CONTEXT_ENABLED": True}
        profile = {
            "system_prompt": "scoped Godmode",
            "prefill": [{"role": "assistant", "content": "primed"}],
        }
        with patch.object(self.handler, "get_activation", return_value=True), \
                patch.object(
                    self.handler, "authorization_status",
                    return_value={"authorization_valid": True},
                ), patch.object(self.handler, "ensure_discovered"), \
                patch.object(self.handler, "effective_profile", return_value={}), \
                patch.object(self.handler, "scoped_profile", return_value=profile), \
                patch.object(self.handler, "mark_context_provided"):
            for mode, expected_system, expected_mode in (
                ("preserve", "", "preserve"),
                ("append", "scoped Godmode", "append"),
                ("override", "scoped Godmode", "replace"),
            ):
                with patch.object(self.handler, "get_system_prompt_mode", return_value=mode):
                    context = self.handler.provide_context("agent-1", "session-1")
                self.assertEqual(context["system_md"], expected_system)
                self.assertEqual(context["system_mode"], expected_mode)
                self.assertEqual(context["prefill_messages"], profile["prefill"])

    def test_refusal_retries_two_program_selected_candidates_then_stops(self):
        self.handler._runtime.clear()
        candidates = [
            {"strategy": "first"},
            {"strategy": "second"},
        ]
        refused = {"score": -9999, "refused": True}
        contexts = [
            {"agent_id": "agent-1", "session_id": "session-1",
             "content": "I cannot help.", "messages": [{"role": "user", "content": "q"}],
             "retry_count": retry_count}
            for retry_count in range(3)
        ]
        with patch.object(self.handler, "get_activation", return_value=True), \
                patch.object(
                    self.handler, "authorization_status",
                    return_value={"authorization_valid": True},
                ), patch.object(
                    self.handler, "score_response", return_value=refused,
                ), patch.object(
                    self.handler, "effective_profile",
                    return_value={"strategy": "none_needed"},
                ), patch.object(
                    self.handler, "_candidate_profiles", return_value=candidates,
                ), patch.object(
                    self.handler, "_candidate_signature",
                    side_effect=lambda _agent, candidate: candidate.get("strategy", "active"),
                ), patch.object(
                    self.handler, "_retry_messages",
                    side_effect=[
                        [{"role": "user", "content": "retry-1"}],
                        [{"role": "user", "content": "retry-2"}],
                    ],
                ), patch.object(
                    self.handler, "get_race_on_failure", return_value=False,
                ), patch.object(self.handler, "mark_response_evaluated") as receipt:
            first = self.handler.evaluate_final_response(contexts[0])
            second = self.handler.evaluate_final_response(contexts[1])
            final = self.handler.evaluate_final_response(contexts[2])

        self.assertTrue(first["retry"])
        self.assertEqual(first["timeline"]["strategy"], "first")
        self.assertTrue(second["retry"])
        self.assertEqual(second["timeline"]["strategy"], "second")
        self.assertNotIn("retry", final)
        self.assertEqual(final["timeline"]["state"], "exhausted")
        self.assertEqual(receipt.call_count, 3)

    def test_non_refusal_is_accepted_without_retry(self):
        self.handler._runtime.clear()
        with patch.object(self.handler, "get_activation", return_value=True), \
                patch.object(
                    self.handler, "authorization_status",
                    return_value={"authorization_valid": True},
                ), patch.object(
                    self.handler, "score_response",
                    return_value={"score": 120, "refused": False},
                ), patch.object(
                    self.handler, "effective_profile",
                    return_value={"strategy": "prefill_only"},
                ), patch.object(self.handler, "mark_response_evaluated"):
            result = self.handler.evaluate_final_response({
                "agent_id": "agent-1", "session_id": "session-1",
                "content": "accepted", "messages": [], "retry_count": 0,
            })
        self.assertEqual(result["content"], "accepted")
        self.assertEqual(result["timeline"]["state"], "not_needed")

    def test_discovery_runs_once_for_the_exact_model(self):
        result = {"success": True, "strategy": "prefill_only"}
        with patch.object(self.handler, "get_automatic_discovery", return_value=True), \
                patch.object(self.handler, "consume_rediscovery", return_value=False), \
                patch.object(
                    self.handler, "_current_model", return_value={"id": "model-1"},
                ), patch.object(
                    self.handler, "_discovery_cached", side_effect=[False, False, True],
                ), patch.object(
                    self.handler.godmode_auto, "execute", return_value=result,
                ) as discover, patch.object(self.handler, "mark_discovery") as receipt:
            self.handler.ensure_discovered("agent-1")
            self.handler.ensure_discovered("agent-1")

        discover.assert_called_once()
        self.assertEqual(receipt.call_args_list[0].args, ("agent-1", "discovering", "model-1"))
        self.assertEqual(receipt.call_args_list[-1].args, ("agent-1", "ready", "model-1"))

    def test_deepseek_runtime_ladder_starts_with_parseltongue(self):
        with patch.object(self.handler, "_current_model", return_value={
            "id": "deepseek-1", "provider": "deepseek", "model_name": "deepseek-chat",
        }):
            candidates = self.handler._candidate_profiles("agent-1")
        self.assertEqual(candidates[0]["strategy"], "parseltongue_L0_PLAIN")
        self.assertEqual(candidates[1]["strategy"], "parseltongue_L1_L33T")


if __name__ == "__main__":
    unittest.main()
