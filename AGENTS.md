# AI coding guidance — ePlus ChatGPT Inspector

An independent, read-only ChatGPT subscription and promotion information tool.

## Do not

- Collect passwords, cookies, tokens, payment information or ChatGPT credentials.
- Add Frida, root, hidden app APIs, BillingClient injection, token extraction, automated purchases or extension attempts.
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
