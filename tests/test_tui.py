"""Headless Textual smoke tests. No network, emulator, or purchases."""

import unittest
from unittest.mock import patch

try:
    from open_ai_inspector.tui import InspectorApp
except ModuleNotFoundError:
    InspectorApp = None


@unittest.skipIf(InspectorApp is None, "Optional Textual dependency is not installed")
class TextualSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_navigation_does_not_open_links_automatically(self):
        app = InspectorApp()
        with patch("open_ai_inspector.tui.open_official_page") as opener:
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.click("#promos")
                await pilot.click("#subscriptions")
                opener.assert_not_called()
                await pilot.click("#google")
                opener.assert_called_once_with("google")

    async def test_smaller_terminal_can_open_dashboard(self):
        app = InspectorApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            self.assertIsNotNone(app.query_one("#report"))


if __name__ == "__main__":
    unittest.main()
