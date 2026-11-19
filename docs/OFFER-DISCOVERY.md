# Offer discovery and verification

Published terms are **not** a guarantee of account eligibility or a claimable promotion.

## Manually researched examples (2026-11-19)

- **Targeted, no published claim deadline:** [U.S. service member and veteran terms](https://help.openai.com/en/articles/12803158-chatgpt-plus-for-service-members-veterans-retirees-terms-of-service). The one-year Plus benefit requires a qualifying service-transition window, an eligible personal account, and ID.me. No published deadline does not mean guaranteed availability.
- **Targeted non-subscription credits:** [Codex for Students](https://help.openai.com/en/articles/20001147-codex-credits-for-students-terms-of-service) offers $100/2,500 Codex usage credits for verified university students in eligible U.S./Canadian institutions. Not Plus and not API credits.
- **Targeted education product:** [ChatGPT for Teachers](https://help.openai.com/en/articles/12844995/) is free through June 2028 for eligible verified U.S. K–12 educators. Not a standard Plus/Pro subscription.
- **Expired:** [2026 Back to School student promotion](https://help.openai.com/en/articles/20001493-chatgpt-back-to-school-offer-for-students). Four free Plus billing periods, for eligible students; claiming ended **October 31, 2026**. Only appears in archived records.

## Automatic discovery (scheduled every 6 hours)

A GitHub Actions job scans selected **public** pages at OpenAI Help Center and OpenAI News. Only promotion-like links to approved official HTTPS domains become candidates marked `pending_review`. It does not query a logged-in account, infer offer eligibility or fetch a Play purchase token.

- Suggestions are deduplicated against the curated references, current and expired programs, and candidates already submitted.
- New leads go to `data/discovered-candidates.json` in a **Draft PR** from `automation/offer-discovery`, never directly to `main`.
- Zero discoveries means no PR. If all official pages are unavailable, the run fails without submitting changes.
- Previously submitted unmerged candidates are retained in the automation branch.
- Reviewers must verify benefit, regional scope, dates, claim URL, account eligibility and any charges before copying anything into the curated catalog.

GitHub Actions pull-request creation requires **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**, in addition to the workflow's declared write permissions. Public sites may block automated reading or change their HTML; this is a best-effort tool, not a complete OpenAI offer feed.

## Local commands

```powershell
python -m open_ai_inspector promos
python -m open_ai_inspector promos --include-expired
python scripts/discover_offers.py
```

Only the discovery script uses public network requests. Offer catalog reads are offline. Never enter or publish private referral links, account credentials or promo codes.
