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

    def test_official_rss_fallback_works_when_html_sources_are_blocked(self):
        rss = """<?xml version="1.0"?><rss version="2.0"><channel>
        <item><title>ChatGPT Go trial promotion announced</title>
        <link>https://openai.com/index/chatgpt-go-trial-announced/</link></item>
        <item><title>General research</title>
        <link>https://openai.com/index/research-paper/</link></item>
        <item><title>ChatGPT Free promotion</title>
        <link>https://openai.com.evil.example/index/chatgpt-free-promo/</link></item>
        </channel></rss>"""
        suggestions, errors, count = discover_candidates(
            self.catalog,
            fetcher=lambda _: (_ for _ in ()).throw(TimeoutError("blocked")),
            roots=(ROOT,),
            feed_roots=("https://openai.com/news/rss.xml",),
            feed_fetcher=lambda _: rss,
        )
        self.assertEqual(count, 1)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].review_status, "pending_review")
        self.assertEqual(suggestions[0].url,
                         "https://openai.com/index/chatgpt-go-trial-announced")
        self.assertTrue(any("unavailable" in error for error in errors))

    def test_rss_never_overrides_already_reviewed_or_seen_entries(self):
        xml = """<rss><channel><item><title>ChatGPT Go trial promotion</title>
            <link>https://openai.com/index/chatgpt-go-trial-announced/</link>
            </item></channel></rss>"""
        suggestions, errors, count = discover_candidates(
            self.catalog, roots=(), previously_seen={
                "https://openai.com/index/chatgpt-go-trial-announced"
            },
            feed_roots=("https://openai.com/news/rss.xml",),
            feed_fetcher=lambda _: xml,
        )
        self.assertEqual(count, 1)
        self.assertEqual(suggestions, [])
        self.assertEqual(errors, [])

    def test_invalid_xml_or_empty_feed_not_counted(self):
        for xml in ("<rss><channel>", "<html><body></body></html>",
                    "<rss><channel></channel></rss>"):
            with self.subTest(xml=xml):
                suggestions, errors, count = discover_candidates(
                    self.catalog, roots=(),
                    feed_roots=("https://openai.com/news/rss.xml",),
                    feed_fetcher=lambda _: xml,
                )
                self.assertEqual(count, 0)
                self.assertEqual(suggestions, [])
                self.assertTrue(any("RSS unavailable" in e for e in errors))

    def test_atom_feed_is_read_as_pending_review_only(self):
        xml = """<feed xmlns="http://www.w3.org/2005/Atom">
            <entry><title>ChatGPT Plus free trial offer details</title>
            <link href="https://openai.com/index/chatgpt-plus-trial/"
             rel="alternate" /></entry>
            </feed>"""
        suggestions, errors, count = discover_candidates(
            self.catalog, roots=(),
            feed_roots=("https://openai.com/news/rss.xml",),
            feed_fetcher=lambda _: xml,
        )
        self.assertEqual(count, 1)
        self.assertFalse(errors)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].review_status, "pending_review")

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
