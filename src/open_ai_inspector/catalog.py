"""Official public promotion catalog: never infers individual eligibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date
from importlib import resources
import json
from pathlib import Path
from urllib.parse import urlsplit


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Reference:
    title: str
    description: str
    url: str


@dataclass(frozen=True)
class PublicOffer:
    title: str
    source_url: str
    region: str
    eligibility: str
    verified_on: str
    expires_on: str | None
    status: str = "terms_published"
    claim_url: str | None = None
    benefit: str = ""
    id: str = ""
    provider: str = "OpenAI"
    offer_type: str = "unknown"
    billing_note: str = ""
    archive_reason: str | None = None  # expired or needs_reverification; never account eligibility


@dataclass(frozen=True)
class Catalog:
    references: tuple[Reference, ...]
    offers: tuple[PublicOffer, ...]
    archived_offers: tuple[PublicOffer, ...] = ()

    def as_dict(self) -> dict:
        return {
            "references": [asdict(item) for item in self.references],
            "offers": [asdict(item) for item in self.offers],
            "archived_offers": [asdict(item) for item in self.archived_offers],
            "eligibility_verified": False,
        }


OFFICIAL_HOSTS = frozenset(("openai.com", "help.openai.com", "chatgpt.com"))
# Exact approved partner domains are allowed for SOURCE DOCUMENTS only,
# never for claim URLs, login redirects, or automated crawler targets.
PARTNER_SOURCE_HOSTS = frozenset(("help.shopee.vn", "www.revolut.com", "www.sea.com", "www.telkomsel.com"))
_OFFER_TYPES = frozenset(("subscription_trial", "subscription_benefit", "paid_discount", "usage_limits", "credits", "education_plan", "unknown"))
_STATUSES = frozenset(("terms_published", "targeted", "expired", "unknown"))


def _text(row: dict, name: str, limit: int = 500) -> str:
    value = row.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CatalogError("Missing/invalid catalog field: " + name)
    return value.strip()


def official_url(value: str) -> str:
    """Reject deceptive hostnames, credentials, query secrets, and untrusted schemes."""
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in OFFICIAL_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or parsed.fragment
        ):
            raise CatalogError("Catalog links must use official HTTPS hosts")
    except ValueError as exc:
        raise CatalogError("Invalid official source URL") from exc
    return value


def source_document_url(value: str) -> str:
    """Allow exact official partner hosts as evidence, never as redemption links."""
    parsed = urlsplit(value)
    if parsed.hostname in OFFICIAL_HOSTS:
        return official_url(value)
    try:
        if (
            parsed.scheme != "https"
            or parsed.hostname not in PARTNER_SOURCE_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or parsed.query
            or parsed.fragment
            or not parsed.path.startswith("/")
        ):
            raise CatalogError("Source link must be an exact approved partner HTTPS domain")
    except ValueError as exc:
        raise CatalogError("Invalid partner source URL") from exc
    return value


def _rows(payload: dict, name: str) -> list:
    values = payload.get(name, [])
    if not isinstance(values, list) or len(values) > 100:
        raise CatalogError(name + " must be a list with no more than 100 entries")
    return values


def load_catalog(path: str | Path | None = None, today: date | None = None) -> Catalog:
    try:
        raw = (
            Path(path).read_text(encoding="utf-8")
            if path is not None
            else resources.files("open_ai_inspector")
                .joinpath("data/official.json").read_text(encoding="utf-8")
        )
        payload = json.loads(raw)
    except (OSError, UnicodeError, ValueError) as exc:
        raise CatalogError("Unable to read valid JSON catalog") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") not in (1, 2):
        raise CatalogError("Unsupported catalog schema")
    references = []
    for row in _rows(payload, "references"):
        if not isinstance(row, dict):
            raise CatalogError("Reference must be an object")
        references.append(Reference(
            _text(row, "title", 120),
            _text(row, "description"),
            official_url(_text(row, "url", 2048)),
        ))

    current = today or date.today()
    offers, archived = [], []
    for row in _rows(payload, "offers"):
        if not isinstance(row, dict):
            raise CatalogError("Offer must be an object")
        raw_end = row.get("expires_on")
        if raw_end is not None and (not isinstance(raw_end, str) or len(raw_end) != 10):
            raise CatalogError("Offer expiration must be YYYY-MM-DD or null")
        raw_claim = row.get("claim_url")
        if raw_claim is not None and not isinstance(raw_claim, str):
            raise CatalogError("Claim URL must be a string or null")
        item = PublicOffer(
            title=_text(row, "title", 120),
            source_url=source_document_url(_text(row, "source_url", 2048)),
            region=_text(row, "region", 60),
            eligibility=_text(row, "eligibility", 500),
            verified_on=_text(row, "verified_on", 10),
            expires_on=raw_end,
            status=row.get("status", "terms_published"),
            claim_url=official_url(raw_claim) if raw_claim else None,
            benefit=row.get("benefit", ""),
            id=row.get("id", ""),
            provider=row.get("provider", "OpenAI"),
            offer_type=row.get("offer_type", "unknown"),
            billing_note=row.get("billing_note", ""),
        )
        if item.status not in _STATUSES:
            raise CatalogError("Unsupported offer status")
        if not isinstance(item.benefit, str) or len(item.benefit) > 200:
            raise CatalogError("Invalid benefit description")
        if not isinstance(item.id, str) or len(item.id) > 100:
            raise CatalogError("Invalid offer identifier")
        if not isinstance(item.provider, str) or not 1 <= len(item.provider) <= 100:
            raise CatalogError("Invalid provider name")
        if item.offer_type not in _OFFER_TYPES:
            raise CatalogError("Invalid offer type")
        if not isinstance(item.billing_note, str) or len(item.billing_note) > 500:
            raise CatalogError("Invalid billing note")
        try:
            reviewed = date.fromisoformat(item.verified_on)
            expiry = date.fromisoformat(item.expires_on) if item.expires_on else None
        except ValueError as exc:
            raise CatalogError("Offer dates must use YYYY-MM-DD") from exc
        if item.status == "expired" or (expiry and expiry < current):
            archived.append(replace(item, archive_reason="expired"))
        elif (current - reviewed).days > 30 or reviewed > current:
            # Old research may still describe a running campaign. Do not call
            # it "expired", but keep it out of recently-reviewed results.
            archived.append(replace(item, archive_reason="needs_reverification"))
        else:
            # No claim deadline does NOT mean perpetual availability.
            # Status remains terms_published or targeted, never "active".
            offers.append(item)
    return Catalog(tuple(references), tuple(offers), tuple(archived))
