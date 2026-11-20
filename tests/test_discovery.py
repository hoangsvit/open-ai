"""Offline discovery tests. No websites, accounts or purchase flows accessed."""

import unittest

from open_ai_inspector.catalog import Catalog, PublicOffer, Reference, CatalogError
from open_ai_inspector.discovery import canonical_url, discover_candidates


ROOT = "https://help.openai.com/en/?q=chatgpt+promotions"
KNOWN = "https://help.openai.com/en/articles/12803158-chatgpt-plus-for-service-members-veterans-retirees-terms-of-service"
NEW = "https://help.openai.com/en/articles/99999999-chatgpt-plus-student-promo"


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(
            references=(Reference("OpenAI FAQ", "Official", "https://help.openai.com/en/articles/123-chatgpt-promo-faq"),),
            offers=(PublicOffer(
                title="Vets", source_url=KNOWN, region="US",
                eligibility="ID.me", verified_on="2026-11-19",
                expires_on=None, status="targeted",
            ),),
        )

    def test_new_official_promotion_links_become_unverified_candidates(self):
        html = f"""
            <a href="/en/articles/99999999-chatgpt-plus-student-promo?utm_source=abc">
                ChatGPT student promo with strict conditions
            </a>
            <a href="{KNOWN}">ChatGPT veterans offer</a>
            <a href="https://help.openai.com.evil.example/en/articles/543-chatgpt-plus-promo">
                ChatGPT offer free
            </a>
            <a href="javascript:alert(1)">ChatGPT promotion</a>
            <a href="/en/articles/321-product-overview">Unrelated product</a>
        """
        proposals, errors, scanned = discover_candidates(
            self.catalog, fetcher=lambda _: html, roots=(ROOT,)
        )
        self.assertEqual(scanned, 1)
        self.assertEqual(errors, [])
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].url, NEW)
        self.assertEqual(proposals[0].review_status, "pending_review")

    def test_repeated_candidate_deduplicated(self):
        html = f'<a href="{NEW}">ChatGPT Student promotion</a>'
        results, _, _ = discover_candidates(
            self.catalog, fetcher=lambda _: html, roots=(ROOT,),
            previously_seen={NEW}
        )
        self.assertEqual(results, [])

    def test_source_failure_never_creates_candidates(self):
        def offline(_):
            raise TimeoutError("source failure")
        proposals, errors, scanned = discover_candidates(
            self.catalog, fetcher=offline, roots=(ROOT,)
        )
        self.assertEqual(proposals, [])
        self.assertEqual(scanned, 0)
        self.assertEqual(len(errors), 1)
        self.assertNotIn("source failure", errors[0])

    def test_js_only_html_is_not_counted_as_valid_scan(self):
        proposals, errors, scanned = discover_candidates(
            self.catalog,
            fetcher=lambda _: '<html><div id="root"></div><script>load()</script></html>',
            roots=(ROOT,),
        )
        self.assertEqual(proposals, [])
        self.assertEqual(scanned, 0)
        self.assertIn("no parseable links", " ".join(errors))

    def test_search_page_without_relevant_articles_has_diagnostic(self):
        html = '<a href="/en/articles/123-product-overview">General docs</a>'
        proposals, errors, scanned = discover_candidates(
            self.catalog, fetcher=lambda _: html, roots=(ROOT,)
        )
        self.assertEqual(proposals, [])
        self.assertEqual(scanned, 1)
        self.assertTrue(any("no promotion-related" in x for x in errors))

    def test_host_allowlist_and_path(self):
        self.assertEqual(canonical_url(NEW + "?campaign=one"), NEW)
        for url in [
            "https://help.openai.com.example.org/en/articles/1-chatgpt-student-promo",
            "http://help.openai.com/en/articles/1-chatgpt-student-promo",
            "https://help.openai.com/other/path",
        ]:
            with self.assertRaises(CatalogError):
                canonical_url(url)


if __name__ == "__main__":
    unittest.main()
