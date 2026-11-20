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

## Android Billing research (optional)

- ADB static inspection and `billing-probe` never prove actual product/offer availability, eligibility, or billing status.
- Runtime Frida class inventory requires direct user opt-in; never run it on startup, during a scheduled job, or when browsing promotions.
- The packaged agent may only enumerate fixed Google Play Billing class names. It must not call/hook BillingClient methods, read fields, dump memory, intercept offer/purchase tokens, submit purchases or interact with checkout.
- Require a pinned Frida runtime with bundled Java bridge; do not silently upgrade/install/root/start a server or attach to multiple ambiguous devices.
- Do not emit device serials or raw Frida/ADB responses in reports. Mock all runtime calls in CI and document that real hardware behavior remains unverified.
