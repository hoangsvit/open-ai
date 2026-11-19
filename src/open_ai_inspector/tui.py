"""Optional Textual interface. Never makes payments or reads account data."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Static

from .catalog import CatalogError, load_catalog
from .device_probe import DeviceResult, probe_android
from .subscriptions import GUIDES, open_official_page

WELCOME = (
    "ePlus ChatGPT Offer Inspector  •  Read-only\n\n"
    "Discover public promotions and view eligibility requirements.\n"
    "Check the official claim terms on the provider website.\n"
    "Optionally inspect the Android app; ADB is not needed for offers.\n\n"
    "This tool cannot confirm personal eligibility, renewal dates, or paid access.\n"
    "No account access, purchase tokens, automated checkout, or subscriptions."
)


class InspectorApp(App):
    TITLE = "ePlus ChatGPT Inspector"
    SUB_TITLE = "Read-only diagnostics and official guidance"
    BINDINGS = [("q", "quit", "Quit"), ("r", "detect", "Detect app")]
    CSS = """
    Screen { background: $surface; }
    #hero { height: 3; padding: 1 2; text-style: bold; }
    #nav { height: 4; margin: 0 1; }
    #nav Button { width: 1fr; margin: 0 1; min-width: 12; }
    #panel { height: 1fr; margin: 0 2 1 2; padding: 1 2; border: round $accent; }
    #report { width: 100%; height: auto; }
    #status { height: 2; padding: 0 2; color: $text-muted; }
    #links { height: 4; margin: 0 1; }
    #links Button { width: 1fr; margin: 0 1; min-width: 12; }
    """

    def __init__(self, adb: str | None = None, serial: str | None = None):
        super().__init__()
        self.adb = adb
        self.serial = serial

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("CHATGPT   /   SUBSCRIPTIONS & PROMOTIONS", id="hero")
        with Horizontal(id="nav"):
            yield Button("Explore offers", id="promos", variant="primary")
            yield Button("Subscription guide", id="subscriptions")
            yield Button("Android tools", id="detect")
        with VerticalScroll(id="panel"):
            yield Static(WELCOME, id="report", markup=False)
        yield Static("No account data accessed  •  No checkout  •  Q to exit", id="status")
        with Horizontal(id="links"):
            yield Button("ChatGPT web", id="web")
            yield Button("Google Play", id="google")
            yield Button("Apple help", id="apple")
        yield Footer()

    def on_mount(self) -> None:
        # Opening the catalog is entirely offline; Android/ADB remains optional.
        self._show_promos()

    def _show(self, content: str, status: str = "Read-only") -> None:
        self.query_one("#report", Static).update(content)
        self.query_one("#status", Static).update(status)

    def action_detect(self) -> None:
        self.query_one("#detect", Button).disabled = True
        self._show("Inspecting Android device using ADB…", "Device inspection in progress")
        self._probe_worker()

    @work(thread=True, exclusive=True)
    def _probe_worker(self) -> None:
        outcome = probe_android(adb=self.adb, serial=self.serial)
        self.call_from_thread(self._show_probe, outcome)

    def _show_probe(self, outcome: DeviceResult) -> None:
        self.query_one("#detect", Button).disabled = False
        installation = (
            "Yes" if outcome.installed else
            "No" if outcome.installed is False else "Unknown"
        )
        self._show(
            "ANDROID APP INSPECTION\n\n"
            f"Result: {outcome.state}\n"
            f"Details: {outcome.message}\n"
            f"Connected devices: {outcome.device_count}\n"
            f"ChatGPT installed: {installation}\n"
            f"App version: {outcome.version or 'Unknown'}\n\n"
            "Subscription: NOT VERIFIED\n"
            "App installation is not proof of ChatGPT Go/Plus/Pro access.",
            "Inspection finished",
        )

    def _show_subscriptions(self) -> None:
        output = [
            "OFFICIAL SUBSCRIPTION MANAGEMENT\n",
            "Use the platform where the original purchase occurred.",
            "Avoid subscribing again on another platform before checking.\n",
        ]
        for platform in ("web", "google", "apple"):
            guide = GUIDES[platform]
            output.extend([guide.title.upper(), guide.instructions, guide.url, ""])
        output.append("The browser links below open only after you click them.")
        self._show("\n".join(output), "Subscription not verified")

    def _show_promos(self) -> None:
        try:
            catalog = load_catalog()
        except CatalogError as exc:
            self._show("Catalog error: " + str(exc), "No offers verified")
            return
        lines = [
            "OFFICIAL PROMOTION RESOURCES\n",
            "These articles explain promotion policies, not available offers.\n",
        ]
        for info in catalog.references:
            lines.extend([info.title, info.description, info.url, ""])
        if not catalog.offers:
            lines.append("No recently reviewed public promotion terms in catalog.")
        else:
            lines.append("PUBLISHED PROMOTION TERMS — eligibility NOT verified\n")
            for offer in catalog.offers:
                lines.extend([
                    offer.title,
                    "Status: " + offer.status + " (not a claimability guarantee)",
                    "Provider: " + offer.provider + " | Type: " + offer.offer_type,
                    "Benefit: " + offer.benefit,
                    "Renewal: " + (offer.billing_note or "See provider terms"),
                    "Region: " + offer.region,
                    "Conditions: " + offer.eligibility,
                    "Claim deadline: " + (offer.expires_on or "not published"),
                    "Terms: " + offer.source_url,
                    "Official claim URL: " + (offer.claim_url or "not published"),
                    "",
                ])
        if catalog.archived_offers:
            lines.append("ARCHIVED PROGRAMS — expired or need renewed verification\n")
            for offer in catalog.archived_offers:
                explanation = (
                    "Claim window ended" if offer.archive_reason == "expired"
                    else "Public evidence is stale; current claimability UNKNOWN"
                )
                lines.extend([
                    offer.title,
                    "Evidence status: " + explanation,
                    "Claim deadline: " + (offer.expires_on or "not published"),
                    "Terms: " + offer.source_url, "",
                ])
        self._show("\n".join(lines), "Offer documentation is not account eligibility")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pressed = event.button.id
        if pressed == "detect":
            self.action_detect()
        elif pressed == "subscriptions":
            self._show_subscriptions()
        elif pressed == "promos":
            self._show_promos()
        elif pressed in GUIDES and not open_official_page(pressed):
            self._show(
                "Could not open the browser. Official URL:\n" + GUIDES[pressed].url,
                "Use your browser to open the URL",
            )
