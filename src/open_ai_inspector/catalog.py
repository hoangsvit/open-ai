"""Human-curated official information; never infers eligibility or active plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass
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
    expires_on: str


@dataclass(frozen=True)
class Catalog:
    references: tuple[Reference, ...]
    offers: tuple[PublicOffer, ...]

    def as_dict(self) -> dict:
        return {
            "references": [asdict(x) for x in self.references],
            "offers": [asdict(x) for x in self.offers],
            "eligibility_verified": False,
        }


def _field(row: dict, name: str, limit: int = 500) -> str:
    value = row.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CatalogError("Missing/invalid field: " + name)
    return value.strip()


def _url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in {"openai.com", "help.openai.com", "chatgpt.com"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
        ):
            raise CatalogError("Source must be an approved official HTTPS URL")
    except ValueError as exc:
        raise CatalogError("Invalid official source URL") from exc
    return url


def _rows(payload: dict, key: str) -> list:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) > 100:
        raise CatalogError("Field must be a list of at most 100 entries: " + key)
    return value


def load_catalog(path: str | Path | None = None, today: date | None = None) -> Catalog:
    try:
        source = (
            Path(path).read_text(encoding="utf-8")
            if path is not None
            else resources.files("open_ai_inspector")
                .joinpath("data/official.json").read_text(encoding="utf-8")
        )
        payload = json.loads(source)
    except (OSError, UnicodeError, ValueError) as exc:
        raise CatalogError("Unable to read valid JSON catalog") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise CatalogError("Unsupported catalog schema")
    references = []
    for row in _rows(payload, "references"):
        if not isinstance(row, dict):
            raise CatalogError("Reference must be an object")
        references.append(Reference(
            _field(row, "title", 120), _field(row, "description"),
            _url(_field(row, "url", 2048)),
        ))
    current = today or date.today()
    offers = []
    for row in _rows(payload, "offers"):
        if not isinstance(row, dict):
            raise CatalogError("Offer must be an object")
        item = PublicOffer(
            _field(row, "title", 120),
            _url(_field(row, "source_url", 2048)),
            _field(row, "region", 60),
            _field(row, "eligibility", 300),
            _field(row, "verified_on", 10),
            _field(row, "expires_on", 10),
        )
        try:
            verified = date.fromisoformat(item.verified_on)
            expires = date.fromisoformat(item.expires_on)
        except ValueError as exc:
            raise CatalogError("Offer dates must use YYYY-MM-DD") from exc
        if 0 <= (current - verified).days <= 30 and current <= expires:
            offers.append(item)
    return Catalog(tuple(references), tuple(offers))
