# AI coding guidance — ePlus ChatGPT Inspector

An independent, read-only ChatGPT subscription and promotion information tool.

## Do not

- Collect passwords, cookies, tokens, payment information or ChatGPT credentials.
- Add Frida method hooks, hidden billing API calls, root escalation, token extraction, automated purchases or extension attempts. The only permitted Frida use is explicit, one-shot, passive loaded-class-name enumeration in a user-authorized environment; no method replacement.
- Claim entitlement, pricing, zero-dollar offers or eligibility without authorized official evidence.
- Print device serials, raw account information, secrets or full sensitive ADB output.
- Auto-open links or initiate checkout without direct user action.

## Engineering requirements

- Keep Python 3.10+ and dependency-free core CLI; Textual is optional.
- Device probe limited to ADB devices, pm path and dumpsys package; shell=False.
- Catalog records must use an official HTTPS URL and expire/stale out. An offer listing is not account eligibility.
- Offline tests must mock ADB; no real purchases or credentials in CI.
- Submit independent Draft PRs; do not directly push implementation to main.
- Follow research scope and unresolved constraints from issue #1.

## Official offer discovery

- New official links are unverified leads, not active offers. Use pending_review candidates and Draft PRs.
- Published terms with no campaign claim deadline must never be labeled "Active"; expiration null means not published.
- Preserve historical expired offers and filter stale (over 30 days since review) from current views.
- Never promote a candidate, refresh verified dates or infer a price based solely on a search snippet.
- Keep automated requests to approved OpenAI public pages with a capped response body and no user credentials.

## Partner offers and redemption

- Allow only precisely vetted partner hosts as documentation sources. No suffix-based host matching or private referral URLs.
- Claim URLs must remain official OpenAI/ChatGPT URLs; documentation URLs are not necessarily claim URLs.
- Separate subscription trials, paid Revolut plan perks, paid continuation discounts and temporary Free usage-limit boosts.
- Archive expired programs; explain paid renewal terms and do not assume an unknown deadline means currently claimable.
- Current scheduled discovery monitors OpenAI public sources, not Shopee/Revolut/Telkomsel. Partner catalog data requires manual verification.

## Status/data integrity regressions

- Always distinguish `expired` from `needs_reverification`; a stale source alone does not prove an offer ended.
- Do not include archived records in default `promos --json`; `--include-archived` explicitly opts in.
- A source returning HTTP 200 with no parseable links is not a successful scan; log non-sensitive diagnostics and fail if no useful source remains.
- Offer-first TUI; Android/ADB is optional and must never trigger on launch.

## Android Billing research (optional)

- ADB static inspection and `billing-probe` never prove actual product/offer availability, eligibility, or billing status.
- Runtime Frida class inventory requires direct user opt-in; never run it on startup, during a scheduled job, or when browsing promotions.
- The packaged agent may only enumerate fixed Google Play Billing class names. It must not call/hook BillingClient methods, read fields, dump memory, intercept offer/purchase tokens, submit purchases or interact with checkout.
- Require a pinned Frida runtime with bundled Java bridge; do not silently upgrade/install/root/start a server or attach to multiple ambiguous devices.
- Do not emit device serials or raw Frida/ADB responses in reports. Mock all runtime calls in CI and document that real hardware behavior remains unverified.

## Public official RSS fallback

- The scheduled HTML crawler may be blocked by OpenAI. Official OpenAI News RSS is allowed as a separate public source, **not** as proof of offer availability.
- Parse only bounded RSS/Atom XML using the strict official OpenAI HTTPS URL checks; no arbitrary feeds, third-party proxies, DTD/entities or dynamic URLs.
- Source outages must remain visible as failures when both HTML and RSS cannot be read. A healthy feed with no eligible articles must not generate artificial candidates or a maintenance PR.
- Preserve manual review and `pending_review` for RSS-derived candidates. Verify live GitHub Actions access separately from offline CI.
