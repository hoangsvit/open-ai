# Android Billing Research — passive, opt-in

This module is an independent **read-only research aid** for the official Android ChatGPT app (`com.openai.chatgpt`). It is inspired by the *diagnostic ergonomics* of `hoangsvit/google-ai`, **not** its Google One Frida billing hooks or checkout stages. No code was copied from its checkout engine.

## What it does

**Static (default, no Frida):** uses authorized ADB commands to detect the ChatGPT application and version and check whether Google Play Store is installed. These facts alone do **not** prove Play Billing integration.

**Runtime (explicit `--runtime`):** optionally attaches Frida to an *already running* ChatGPT process and uses one-shot Java class enumeration. It reports only the names of a hard-coded small allowlist of Google Play Billing Library classes found loaded at that moment, such as `com.android.billingclient.api.BillingClient`. It detaches after the check.

**What it does NOT do:** query products or introductory offers, call `queryProductDetailsAsync`, read `getOfferToken`, observe purchase tokens, read accounts/cookies, hook/replace app methods, start apps or checkout, call `launchBillingFlow`, or confirm eligibility/entitlements. Loaded BillingClient classes may be present even when no valid promotional offer exists. Missing loaded classes do **not** establish the app lacks Billing integration: code can load lazily, be obfuscated, or use a different payment path.

## Commands

```powershell
# Install the normal optional Textual UI, if desired
python -m pip install -e ".[tui]"

# Static ADB-only check; no Frida required, no checkout
python -m open_ai_inspector billing-probe
python -m open_ai_inspector billing-probe --json

# Install the optional pinned version only in a user-managed test environment
python -m pip install -e ".[billing]"

# Start ChatGPT on an Android device/emulator you own and authorize,
# and separately start a matching Frida server (not managed by this tool).
python -m open_ai_inspector billing-probe --runtime --json

# For multiple Android devices, explicitly select *both* ADB and Frida devices:
python -m open_ai_inspector billing-probe --serial emulator-5554 --frida-device-id YOUR_FRIDA_ID --runtime
```

Runtime is **never** invoked on app startup, in TUI or during ordinary `promos` commands. If Frida is missing/incompatible or the app is not already running, the tool prints a sanitized diagnostic and stops. All statuses are advisory; no account or financial information is returned.

## Why Frida 16.5.9 is pinned

Frida 17 removed the bundled Java bridge in standalone GumJS scripts. Supporting Frida 17 requires bundling `frida-java-bridge`, which is intentionally out of scope. The optional package is pinned to 16.5.9 to match the legacy API. This older version may not support all Android versions or security environments. Installing a package does not configure root, open ADB, run Frida server, or guarantee attach compatibility.

- [Frida 17 release explanation](https://frida.re/news/2025/05/17/frida-17-0-0-released/)
- [Frida JavaScript API](https://frida.re/docs/javascript-api/)
- [Google Play Billing integration](https://developer.android.com/google/play/billing/integrate)
- [Google Play subscriptions](https://developer.android.com/google/play/billing/subscriptions)

## Privacy and safety

- No device serials, account IDs, emails or raw ADB/Frida messages are written to the console or JSON report.
- Only a fixed list of Billing class names may be copied from the Frida message.
- No `--force`, `adb root`, installation, payment operations, interception, offer token access or unauthorized billing API invocation.
- A Frida attach has intrinsic crash/stability risk: use a test device/emulator with consent, not a production device or sensitive session.
- There is **no verified ChatGPT Android offer metadata or redemption** in this module. Use the official ChatGPT/Google Play subscription management interface to verify real entitlements.

## Test scope

CI runs deterministic fake ADB and Frida tests only. It verifies no purchase operations are called by the Python probe, sanitization, multi-device guardrails, Frida version compatibility and clean detach. Live runtime compatibility remains **not tested**.
