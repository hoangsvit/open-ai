import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from open_ai_inspector.catalog import CatalogError, load_catalog


class CatalogTests(unittest.TestCase):
    def write(self, data):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "catalog.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_default_contains_documented_veterans_and_expired_student_offer(self):
        result = load_catalog(today=date(2026, 11, 19))
        self.assertGreaterEqual(len(result.references), 2)
        self.assertEqual(len(result.offers), 3)
        self.assertEqual(result.offers[0].status, "targeted")
        self.assertIsNone(result.offers[0].expires_on)
        self.assertIn("ID.me", result.offers[0].eligibility)
        self.assertTrue(any("Codex" in x.title and "not a Plus" in x.title for x in result.offers))
        self.assertTrue(any("Teachers" in x.title for x in result.offers))
        self.assertEqual(len(result.archived_offers), 1)
        self.assertEqual(result.archived_offers[0].status, "expired")
        self.assertFalse(result.as_dict()["eligibility_verified"])

    def test_stale_documented_program_is_not_shown_as_current(self):
        result = load_catalog(today=date(2027, 1, 19))
        self.assertFalse(result.offers)
        self.assertEqual(len(result.archived_offers), 4)

    def test_only_fresh_unexpired_offers(self):
        day = date(2026, 11, 19)
        def offer(title, reviewed, expiry):
            return {
                "title": title,
                "source_url": "https://help.openai.com/en/articles/1",
                "region": "US",
                "eligibility": "Unknown for the user",
                "verified_on": reviewed.isoformat(),
                "expires_on": expiry.isoformat(),
            }
        data = {"schema_version": 1, "references": [], "offers": [
            offer("current", day - timedelta(days=1), day + timedelta(days=7)),
            offer("expired", day - timedelta(days=4), day - timedelta(days=1)),
            offer("stale", day - timedelta(days=31), day + timedelta(days=7)),
        ]}
        result = load_catalog(self.write(data), day)
        self.assertEqual([x.title for x in result.offers], ["current"])

    def test_reject_fake_domain(self):
        data = {"schema_version": 1, "references": [
            {"title": "bad", "description": "bad",
             "url": "https://help.openai.com.evil.example/"}], "offers": []}
        with self.assertRaises(CatalogError):
            load_catalog(self.write(data))

    def test_reject_javascript_link(self):
        data = {"schema_version": 1, "references": [
            {"title": "bad", "description": "bad",
             "url": "javascript:alert(1)"}], "offers": []}
        with self.assertRaises(CatalogError):
            load_catalog(self.write(data))

    def test_invalid_json(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "catalog.json"
        path.write_text("not valid json", encoding="utf-8")
        with self.assertRaises(CatalogError):
            load_catalog(path)

    def test_bad_dates(self):
        data = {"schema_version": 1, "references": [], "offers": [
            {"title": "bad", "source_url": "https://chatgpt.com/",
             "region": "US", "eligibility": "unknown",
             "verified_on": "n/a", "expires_on": "2027-01-01"}]}
        with self.assertRaises(CatalogError):
            load_catalog(self.write(data))


if __name__ == "__main__":
    unittest.main()
