"""Read-only CLI. Textual is optional and imported only when requested."""

from __future__ import annotations

import argparse
import json
import sys

from .catalog import CatalogError, load_catalog
from .device_probe import probe_android
from .subscriptions import guide_for, open_official_page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="open-ai-inspector",
        description="Read-only ChatGPT Android and subscription inspector.",
    )
    cmds = parser.add_subparsers(dest="command")
    inspect = cmds.add_parser("inspect", help="Detect official ChatGPT Android app with ADB")
    inspect.add_argument("--adb", help="Optional ADB executable path")
    inspect.add_argument("--serial", help="Device serial from adb devices")
    inspect.add_argument("--json", action="store_true")

    subs = cmds.add_parser("subscriptions", help="Official subscription-management guidance")
    subs.add_argument("--platform", choices=["web", "google", "apple"], default="web")
    subs.add_argument("--open", action="store_true", help="Open official URL in browser")

    offers = cmds.add_parser("promos", help="Official resources and dated public offers")
    offers.add_argument("--catalog", help="Optional local JSON catalog")
    offers.add_argument("--json", action="store_true")
    offers.add_argument("--include-expired", action="store_true", help="Show archived or stale promotions")

    billing = cmds.add_parser(
        "billing-probe",
        help="Read-only Android Play Billing integration research (no offer tokens or checkout)",
    )
    billing.add_argument("--adb", help="Optional path to ADB executable")
    billing.add_argument("--serial", help="ADB serial if multiple Android devices are connected")
    billing.add_argument(
        "--runtime", action="store_true",
        help="Opt in to attaching Frida 16.5.9 to the running app for class-name inventory",
    )
    billing.add_argument("--frida-device-id", help="Explicit Frida device ID for runtime inspection")
    billing.add_argument("--json", action="store_true", help="Print sanitized structured report")

    tui = cmds.add_parser("tui", help="Interactive Textual dashboard")
    tui.add_argument("--adb")
    tui.add_argument("--serial")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "tui"
    if command == "inspect":
        result = probe_android(adb=args.adb, serial=args.serial)
        if args.json:
            print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        else:
            print(result.message)
            print("App installed:", result.installed if result.installed is not None else "Unknown")
            if result.version:
                print("Version:", result.version)
            print("Subscription and eligibility: NOT VERIFIED")
        return 0 if result.state == "detected" else 1

    if command == "subscriptions":
        guide = guide_for(args.platform)
        print(guide.title + "\n" + guide.instructions + "\n" + guide.url)
        print("Your subscription status cannot be verified by this tool.")
        if args.open and not open_official_page(args.platform):
            print("Browser did not open; use the URL above.", file=sys.stderr)
            return 1
        return 0

    if command == "promos":
        try:
            catalog = load_catalog(args.catalog)
        except CatalogError as exc:
            print("Catalog error: " + str(exc), file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(catalog.as_dict(), ensure_ascii=False, indent=2))
        else:
            print("Official information resources:")
            for ref in catalog.references:
                print("  " + ref.title + ": " + ref.url)
            if not catalog.offers:
                print("No recently reviewed public promotion terms in the catalog.")
            else:
                print("Documented programs (availability and account eligibility NOT guaranteed):")
                for offer in catalog.offers:
                    print("  " + offer.title + " [" + offer.region + "]")
                    print("  Status: " + offer.status + " | Claim deadline: " +
                          (offer.expires_on or "not published"))
                    print("  Provider: " + offer.provider + " | Type: " + offer.offer_type)
                    print("  Benefit: " + offer.benefit)
                    if offer.billing_note:
                        print("  Billing/renewal: " + offer.billing_note)
                    print("  Eligibility: " + offer.eligibility)
                    print("  Terms: " + offer.source_url)
                    if offer.claim_url:
                        print("  Official claim page: " + offer.claim_url)
            if args.include_expired:
                print("Expired or stale programs (NOT currently claimable):")
                for offer in catalog.archived_offers:
                    print("  Provider: " + offer.provider + " | Type: " + offer.offer_type)
                    print("  " + offer.title + " | ended: " +
                          (offer.expires_on or "not confirmed") + " | " + offer.source_url)
        return 0

    if command == "billing-probe":
        from .billing_research import inspect_billing
        outcome = inspect_billing(
            adb=args.adb, serial=args.serial, runtime=args.runtime,
            frida_device_id=args.frida_device_id,
        )
        if args.json:
            print(json.dumps(outcome.as_dict(), ensure_ascii=False, indent=2))
        else:
            print("Android Billing research:", outcome.state)
            print("ChatGPT installed:", outcome.app_installed)
            print("Google Play installed:", outcome.play_store_installed)
            print("ChatGPT version:", outcome.app_version or "unknown")
            print("Frida runtime:", outcome.runtime_status)
            if outcome.billing_library_loaded is not None:
                print("Google Play Billing class observed:", outcome.billing_library_loaded)
                print("Loaded class names:", ", ".join(outcome.billing_classes_loaded) or "none")
            print(outcome.message)
            print("Personal eligibility: NOT VERIFIED; subscription: NOT VERIFIED")
            print("No offer query, purchase token access or checkout was performed.")
        if outcome.state != "inspected":
            return 1
        return 0 if outcome.runtime_status in ("not_requested", "complete") else 2

    if command == "tui":
        try:
            from .tui import InspectorApp
        except ModuleNotFoundError as exc:
            if exc.name and (exc.name == "textual" or exc.name.startswith("textual.")):
                print('Install UI: python -m pip install -e ".[tui]"', file=sys.stderr)
                return 2
            raise
        InspectorApp(adb=getattr(args, "adb", None),
                     serial=getattr(args, "serial", None)).run()
        return 0
    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
