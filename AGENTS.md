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
