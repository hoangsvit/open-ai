import contextlib
import io
import json
import unittest
from unittest.mock import patch

from open_ai_inspector.cli import main
from open_ai_inspector.device_probe import DeviceResult
from open_ai_inspector.subscriptions import GUIDES, guide_for


class CliTests(unittest.TestCase):
    def test_json_output_never_claims_subscription(self):
        out = io.StringIO()
        with patch("open_ai_inspector.cli.probe_android",
                   return_value=DeviceResult("detected", "Installed", 1, True, "1.0")), \
             contextlib.redirect_stdout(out):
            status = main(["inspect", "--json"])
        result = json.loads(out.getvalue())
        self.assertEqual(status, 0)
        self.assertTrue(result["installed"])
        self.assertNotIn("subscription_active", result)

    def test_subscriptions_never_open_browser_by_default(self):
        out = io.StringIO()
        with patch("open_ai_inspector.cli.open_official_page") as fn, \
             contextlib.redirect_stdout(out):
            result = main(["subscriptions", "--platform", "google"])
        self.assertEqual(result, 0)
        self.assertIn(GUIDES["google"].url, out.getvalue())
        fn.assert_not_called()

    def test_promos_never_invent_offers(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = main(["promos"])
        self.assertEqual(result, 0)
        self.assertIn("Documented programs", out.getvalue())
        self.assertIn("Claim deadline: not published", out.getvalue())
        self.assertIn("eligibility NOT guaranteed", out.getvalue())

    def test_json_archive_flag_and_legacy_alias(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["promos", "--json"]), 0)
        data = json.loads(out.getvalue())
        self.assertIn("offers", data)
        self.assertNotIn("archived_offers", data)

        for flag in ("--include-expired", "--include-archived"):
            with self.subTest(flag=flag):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(main(["promos", "--json", flag]), 0)
                result = json.loads(out.getvalue())
                self.assertGreater(len(result["archived_offers"]), 0)
                self.assertTrue(all(x["archive_reason"] for x in result["archived_offers"]))

    def test_only_approved_platforms(self):
        for platform in ("web", "google", "apple"):
            self.assertTrue(guide_for(platform).url.startswith("https://"))
        with self.assertRaises(ValueError):
            guide_for("invalid")


if __name__ == "__main__":
    unittest.main()
