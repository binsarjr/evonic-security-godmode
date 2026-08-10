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
            "register_agent_state_summary_provider",
            "register_turn_context_provider",
            "register_user_message_transformer",
            "unregister_agent_state_summary_provider",
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


if __name__ == "__main__":
    unittest.main()
