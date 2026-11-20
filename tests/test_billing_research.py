"""Offline tests for the passive Android Billing research probe.

Never launches Frida, BillingClient, Play Store checkout, or a real emulator.
"""

import contextlib
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from open_ai_inspector.billing_research import (
    BILLING_CLASSES,
    _class_probe,
    inspect_billing,
)
from open_ai_inspector.cli import main


def fake_adb(devices="phone01\tdevice\n", chatgpt=True, store=True):
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == "devices":
            stdout = "List of devices attached\n" + devices
        elif argv[-3:] == ["pm", "path", "com.openai.chatgpt"]:
            stdout = "package:/data/app/chatgpt/base.apk" if chatgpt else ""
        elif argv[-3:] == ["pm", "path", "com.android.vending"]:
            stdout = "package:/system/app/Phonesky.apk" if store else ""
        elif "dumpsys" in argv:
            stdout = "versionName=1.2.3"
        else:
            raise AssertionError("Unexpected ADB command: " + repr(argv))
        return SimpleNamespace(returncode=0, stdout=stdout)

    return runner, calls


class FakeScript:
    def __init__(self, payload):
        self.callback = None
        self.payload = payload
        self.unloaded = False
        self.source = None

    def on(self, name, callback):
        assert name == "message"
        self.callback = callback

    def load(self):
        assert self.callback is not None
        self.callback({"type": "send", "payload": self.payload}, None)

    def unload(self):
        self.unloaded = True


class FakeSession:
    def __init__(self, payload):
        self.script = FakeScript(payload)
        self.detached = False

    def create_script(self, source):
        self.script.source = source
        return self.script

    def detach(self):
        self.detached = True


class FakeDevice:
    def __init__(self, payload):
        self.session = FakeSession(payload)
        self.attached = []

    def attach(self, name):
        self.attached.append(name)
        return self.session


def fake_frida(payload, version="16.5.9"):
    device = FakeDevice(payload)
    return SimpleNamespace(
        __version__=version,
        get_usb_device=lambda **kwargs: device,
        get_device=lambda *args, **kwargs: device,
    ), device


class BillingResearchTests(unittest.TestCase):
    def test_static_probe_never_imports_frida_or_queries_billing(self):
        runner, calls = fake_adb()
        with patch.dict("sys.modules", {"frida": None}):
            result = inspect_billing(adb="adb", runner=runner)
        self.assertEqual(result.state, "inspected")
        self.assertTrue(result.app_installed)
        self.assertTrue(result.play_store_installed)
        self.assertEqual(result.app_version, "1.2.3")
        self.assertEqual(result.runtime_status, "not_requested")
        self.assertIsNone(result.billing_library_loaded)
        self.assertFalse(result.eligibility_verified)
        self.assertFalse(result.subscription_verified)
        self.assertFalse(result.checkout_attempted)
        self.assertFalse(any("root" in " ".join(cmd) for cmd in calls))
        self.assertFalse(any("purchase" in " ".join(cmd) for cmd in calls))
        self.assertNotIn("phone01", json.dumps(result.as_dict()))

    def test_missing_chatgpt_does_not_attempt_runtime(self):
        runner, calls = fake_adb(chatgpt=False)
        frida, device = fake_frida({"type": "billing_class_probe", "java_available": True, "loaded_classes": []})
        result = inspect_billing(adb="adb", runner=runner, runtime=True, frida_module=frida)
        self.assertEqual(result.state, "app_missing")
        self.assertEqual(result.runtime_status, "not_attempted")
        self.assertFalse(device.attached)
        self.assertEqual(len(calls), 2)

    def test_play_store_missing_does_not_confirm_no_billing(self):
        runner, _ = fake_adb(store=False)
        result = inspect_billing(adb="adb", runner=runner)
        self.assertFalse(result.play_store_installed)
        self.assertIsNone(result.billing_library_loaded)

    def test_frida_not_installed_gives_actionable_status(self):
        runner, _ = fake_adb()
        with patch.dict("sys.modules", {"frida": None}):
            result = inspect_billing(adb="adb", runner=runner, runtime=True)
        self.assertEqual(result.runtime_status, "frida_missing")
        self.assertIsNone(result.billing_library_loaded)

    def test_runtime_observes_allowlisted_classes_only(self):
        runner, _ = fake_adb()
        payload = {
            "type": "billing_class_probe",
            "java_available": True,
            "loaded_classes": [BILLING_CLASSES[0], BILLING_CLASSES[2]],
            "token": "private-must-not-be-exposed",
        }
        frida, device = fake_frida(payload)
        result = inspect_billing(adb="adb", runtime=True, runner=runner, frida_module=frida)
        self.assertEqual(result.runtime_status, "complete")
        self.assertTrue(result.billing_library_loaded)
        self.assertEqual(result.billing_classes_loaded, (BILLING_CLASSES[0], BILLING_CLASSES[2]))
        self.assertEqual(device.attached, ["com.openai.chatgpt"])
        self.assertTrue(device.session.script.unloaded)
        self.assertTrue(device.session.detached)
        self.assertNotIn("private-must-not-be-exposed", str(result.as_dict()))
        self.assertNotIn("launchBillingFlow", device.session.script.source)
        self.assertNotIn("getOfferToken", device.session.script.source)

    def test_runtime_no_loaded_classes_is_not_proof_of_no_integration(self):
        runner, _ = fake_adb()
        frida, _ = fake_frida({"type": "billing_class_probe", "java_available": True, "loaded_classes": []})
        result = inspect_billing(adb="adb", runtime=True, runner=runner, frida_module=frida)
        self.assertEqual(result.runtime_status, "complete")
        self.assertFalse(result.billing_library_loaded)
        self.assertFalse(result.eligibility_verified)

    def test_rejects_unexpected_agent_payload(self):
        frida, device = fake_frida({
            "type": "billing_class_probe",
            "java_available": True,
            "loaded_classes": ["com.other.secret.Account"],
        })
        status, names, message = _class_probe(frida, None, timeout=0)
        self.assertEqual(status, "invalid_agent_result")
        self.assertEqual(names, ())
        self.assertNotIn("Account", message)
        self.assertTrue(device.session.detached)

    def test_runtime_rejects_frida17_until_java_bridge_is_bundled(self):
        runner, _ = fake_adb()
        frida, device = fake_frida(None, version="17.0.0")
        result = inspect_billing(adb="adb", runner=runner, runtime=True, frida_module=frida)
        self.assertEqual(result.runtime_status, "unsupported_frida")
        self.assertFalse(device.attached)

    def test_multiple_devices_require_both_explicit_identifiers(self):
        runner, _ = fake_adb(devices="phone01\tdevice\nphone02\tdevice\n")
        frida, device = fake_frida(None)
        result = inspect_billing(adb="adb", serial="phone01", runner=runner, runtime=True, frida_module=frida)
        self.assertEqual(result.runtime_status, "device_selection_required")
        self.assertFalse(device.attached)

    def test_cli_json_contains_no_sensitive_fields(self):
        runner, _ = fake_adb()
        fake_result = inspect_billing(adb="adb", runner=runner)
        output = io.StringIO()
        with patch("open_ai_inspector.billing_research.inspect_billing", return_value=fake_result), \
             contextlib.redirect_stdout(output):
            self.assertEqual(main(["billing-probe", "--json"]), 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["state"], "inspected")
        self.assertFalse(data["eligibility_verified"])
        self.assertNotIn("serial", data)
        self.assertNotIn("token", data)


if __name__ == "__main__":
    unittest.main()
