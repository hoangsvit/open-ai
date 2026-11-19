import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from open_ai_inspector.device_probe import probe_android


def make_runner(devices, package="package:/data/app/base.apk", version="versionName=1.2.3"):
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == "devices":
            stdout = "List of devices attached\n" + devices
        elif "pm" in argv:
            stdout = package
        elif "dumpsys" in argv:
            stdout = version
        else:
            raise AssertionError("Unexpected command")
        return SimpleNamespace(returncode=0, stdout=stdout)
    return run, calls


class DeviceProbeTests(unittest.TestCase):
    def test_adb_missing(self):
        with patch("open_ai_inspector.device_probe.shutil.which", return_value=None):
            result = probe_android()
        self.assertEqual(result.state, "adb_missing")
        self.assertIsNone(result.installed)

    def test_unauthorized(self):
        runner, calls = make_runner("emulator-5554\tunauthorized\n")
        self.assertEqual(probe_android(adb="adb", runner=runner).state, "unauthorized")
        self.assertEqual(len(calls), 1)

    def test_offline(self):
        runner, _ = make_runner("emulator-5554\toffline\n")
        self.assertEqual(probe_android(adb="adb", runner=runner).state, "offline")

    def test_many_devices_must_choose_one(self):
        runner, calls = make_runner("phone01\tdevice\nphone02\tdevice\n")
        self.assertEqual(probe_android(adb="adb", runner=runner).state, "multiple_devices")
        self.assertEqual(len(calls), 1)

    def test_selected_device_not_found(self):
        runner, calls = make_runner("phone01\tdevice\n")
        result = probe_android(adb="adb", serial="phone02", runner=runner)
        self.assertEqual(result.state, "device_not_found")
        self.assertEqual(len(calls), 1)

    def test_installed_app_does_not_imply_subscription(self):
        runner, calls = make_runner("emulator-5554\tdevice\n")
        result = probe_android(adb="adb", runner=runner)
        self.assertEqual(result.state, "detected")
        self.assertTrue(result.installed)
        self.assertEqual(result.version, "1.2.3")
        self.assertNotIn("emulator-5554", str(result.as_dict()))
        self.assertTrue(any("com.openai.chatgpt" in cmd for cmd in calls))
        self.assertFalse(any("purchase" in str(cmd).lower() for cmd in calls))

    def test_app_missing(self):
        runner, _ = make_runner("phone01\tdevice\n", package="")
        result = probe_android(adb="adb", runner=runner)
        self.assertEqual(result.state, "app_missing")
        self.assertFalse(result.installed)

    def test_hide_invalid_version_text(self):
        runner, _ = make_runner("phone01\tdevice\n", version="versionName=<sensitive>")
        self.assertIsNone(probe_android(adb="adb", runner=runner).version)

    def test_adb_error_is_sanitized(self):
        def runner(argv, **kwargs):
            return SimpleNamespace(returncode=1, stdout="account@example.com")
        result = probe_android(adb="adb", runner=runner)
        self.assertEqual(result.state, "adb_error")
        self.assertNotIn("@", result.message)

    def test_timeout(self):
        def runner(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, 10)
        self.assertEqual(probe_android(adb="adb", runner=runner).state, "adb_error")


if __name__ == "__main__":
    unittest.main()
