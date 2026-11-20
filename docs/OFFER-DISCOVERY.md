# Offer discovery and verification

Published terms are **not** a guarantee of account eligibility or a claimable promotion.

## Manually researched examples (2026-11-19)

- **Targeted, no published claim deadline:** [U.S. service member and veteran terms](https://help.openai.com/en/articles/12803158-chatgpt-plus-for-service-members-veterans-retirees-terms-of-service). The one-year Plus benefit requires a qualifying service-transition window, an eligible personal account, and ID.me. No published deadline does not mean guaranteed availability.
- **Targeted non-subscription credits:** [Codex for Students](https://help.openai.com/en/articles/20001147-codex-credits-for-students-terms-of-service) offers $100/2,500 Codex usage credits for verified university students in eligible U.S./Canadian institutions. Not Plus and not API credits.
- **Targeted education product:** [ChatGPT for Teachers](https://help.openai.com/en/articles/12844995/) is free through June 2028 for eligible verified U.S. K–12 educators. Not a standard Plus/Pro subscription.
- **Expired:** [2026 Back to School student promotion](https://help.openai.com/en/articles/20001493-chatgpt-back-to-school-offer-for-students). Four free Plus billing periods, for eligible students; claiming ended **October 31, 2026**. Only appears in archived records.

## Regional trials, introductory offers and partner benefits (researched 2026-11-19)

| Program | Benefit | Claim deadline | Restrictions |
| --- | --- | --- | --- |
| [India Go promotional year](https://help.openai.com/en/articles/6825453-chatgpt-release-notes) | Go free for 12 months | **Ended 2026-01-21** | India-based Free, new or existing Go customers; card or UPI |
| [India Go continuation](https://help.openai.com/en/articles/20001631-chatgpt-go-india-trial-renewals-and-continuation-offers) | **Paid** discount for 3 billing periods, not a second free year | Not published | Offered only in the eligible original trial account |
| [ShopeeVIP Vietnam Go](https://help.shopee.vn/portal/4/article/191651) | Go free 3 months | **Ended 2026-05-31** | Active ShopeeVIP, new paid-ChatGPT subscriber, Vietnam account, card required |
| [Revolut Standard/Plus Go trial](https://www.revolut.com/legal/chatgpt-3-months-trial-offer/) | Go free 3 months | **2027-07-29** published deadline | Invited Revolut customer aged 18+, eligible country, no ChatGPT subscription during previous 3 months |
| [Revolut paid-plan Go benefit](https://www.revolut.com/de-DE/news/revolut_partners_with_openai_to_bring_chatgpt_go_to_millions_of_customers/) | Go 6–12 months depending on plan | Not published | Revolut Premium/Pro/Mobile/Metal/Ultra paid membership, country and account conditions |
| [ChatGPT Free referral](https://help.openai.com/en/articles/20001479-chatgpt-free-referral-campaign) | 2x Free usage limit for up to 21 days; **not Plus/Go** | **Ended 2026-09-17** | Selected users in India, Indonesia, Mexico |
| [Telkomsel Go bundle](https://www.telkomsel.com/jelajah/jelajah-lifestyle/promo-telkomsel-paket-chatgpt-bikin-kerjaan-lebih-simpel) | Paid mobile data package including ChatGPT Go | **Ended 2026-05-31** | Eligible Telkomsel customers |

**Additional Shopee announcement:** [Sea's official December 2025 release](https://www.sea.com/news/377) announced one-month Go access for Shopee customers across five markets starting January 2026. It lacks a recently confirmed claim period, so it is not presented as claimable in the catalog.

**Safety and semantics:** Offer source documents can be linked only from OpenAI or vetted exact partner domains (Shopee, Revolut, Sea, Telkomsel); the claim URL still only accepts official OpenAI/ChatGPT domains. No personal referral or promo codes are stored. A documented program is not proof an account can claim it, and a missing claim deadline is never assumed to mean permanently available.

**Renewal:** Revolut's Standard/Plus trial converts to monthly paid Go unless cancelled in time. Shopee trial also had paid renewal rules, while some original ShopeeVIP benefits ended if the ShopeeVIP subscription was cancelled. Users must check exact checkout terms themselves.

## Automatic discovery (scheduled every 6 hours)

A GitHub Actions job scans selected **public** pages at OpenAI Help Center and OpenAI News. **Partner offers are researched manually**; current scheduled discovery does not crawl Shopee, Revolut or Telkomsel. Only promotion-like links to approved official HTTPS domains become candidates marked `pending_review`. It does not query a logged-in account, infer offer eligibility or fetch a Play purchase token.

- Suggestions are deduplicated against the curated references, current and expired programs, and candidates already submitted.
- New leads go to `data/discovered-candidates.json` in a **Draft PR** from `automation/offer-discovery`, never directly to `main`.
- Zero verified new links means no PR. If all official pages are unavailable **or return no parseable public links**, the run fails without submitting changes. An HTML page with unrelated links produces a warning, not a false success claim about offer coverage.
- Previously submitted unmerged candidates are retained in the automation branch.
- Reviewers must verify benefit, regional scope, dates, claim URL, account eligibility and any charges before copying anything into the curated catalog.

GitHub Actions pull-request creation requires **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**, in addition to the workflow's declared write permissions. Public sites may block automated reading or change their HTML; this is a best-effort tool, not a complete OpenAI offer feed.

## Local commands

```powershell
python -m open_ai_inspector promos
python -m open_ai_inspector promos --include-archived
python -m open_ai_inspector promos --json --include-archived
python scripts/discover_offers.py
```

Only the discovery script uses public network requests. Offer catalog reads are offline. Never enter or publish private referral links, account credentials or promo codes.

## Offer evidence freshness

- `archive_reason=expired`: the published deadline passed or the program was explicitly marked expired.
- `archive_reason=needs_reverification`: the evidence is more than 30 days old or dated in the future; **do not claim the promotion ended**. It may remain available, but current eligibility must be reconfirmed.
- Neither a public source nor a successful crawler run confirms personal eligibility or a completed redemption.
- A scheduled job can be tested by opening GitHub **Actions → Offer discovery → Run workflow** after merge. Inspect the actual logs for parseable links, source warnings and GitHub's permission to create Draft PRs.
