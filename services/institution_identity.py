import os
import re
import time
import unicodedata
from functools import lru_cache
from typing import Any
from urllib.parse import quote, urlsplit

import httpx
from fastapi import HTTPException

NINJAS_URL = "https://api.api-ninjas.com/v1/university"
STUDID_ENTITY_URL = "https://api.studid.io/v2/entities/"


def normalized_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    value = unicodedata.normalize("NFKD", value).casefold()

    return "".join(character for character in value 
        if character.isalnum() and not unicodedata.combining(character)
    )


def hostname(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""

    try:
        parsed = urlsplit(
            value if "://" in value else "https://" + value
        )
        host = ((parsed.hostname or "").encode("idna").decode().lower() .rstrip("."))
    except (ValueError, UnicodeError):
        return ""

    return host.removeprefix("www.")


def clean_domain(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    domain = value.strip().lower().rstrip(".")

    if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}", domain):
        return ""

    return domain


def domain_matches(domain: str, allowed_domains: list[str]) -> bool:
    domain = clean_domain(domain)

    if not domain:
        return False

    for value in allowed_domains:
        allowed = clean_domain(value)

        if not allowed or allowed == "edu":
            continue

        if domain == allowed or domain.endswith("." + allowed):
            return True

    return False


def institution_names(record: dict[str, Any]) -> set[str]:
    values = [record.get("name", ""), record.get("native_name", "")]

    aliases = record.get("aliases", [])

    if isinstance(aliases, list):
        values.extend(aliases)

    return {normalized_name(value) for value in values if isinstance(value, str) and value.strip()}


def same_institution(
    scorecard: dict[str, Any],
    candidate: dict[str, Any],
) -> bool:
    if candidate.get("country_code") != "US":
        return False

    if candidate.get("status", "active") != "active":
        return False

    name = normalized_name(scorecard.get("name"))

    if not name or name not in institution_names(candidate):
        return False

    if (
        str(candidate.get("state", "")).upper()
        != str(scorecard.get("state", "")).upper()
    ):
        return False

    city = normalized_name(scorecard.get("city"))

    if not city or city != normalized_name(candidate.get("city")):
        return False

    official_host = hostname(scorecard.get("school_url"))
    candidate_host = hostname(candidate.get("website"))
    domains = candidate.get("domains", [])

    if not isinstance(domains, list):
        return False

    return bool(official_host and candidate_host
        and official_host == candidate_host
        and domain_matches(official_host, domains))


@lru_cache(maxsize=512)
def _search_universities(
    query: str,
    cache_bucket: int,
) -> tuple[dict[str, Any], ...]:
    key = os.environ.get("API_NINJAS_API_KEY", "")

    if not key:
        raise HTTPException(
            503,
            "Institution lookup is not configured.",
        )

    try:
        response = httpx.get(
            NINJAS_URL,
            params={
                "name": query,
                "country": "USA",
                "limit": 30,
            },
            headers={
                "X-Api-Key": key,
                "User-Agent": "SmartCampusAssistant/1.0",
            },
            timeout=15,
            follow_redirects=False,
        )
        response.raise_for_status()
        rows = response.json()

        if (
            not isinstance(rows, list)
            or any(not isinstance(row, dict) for row in rows)
        ):
            raise ValueError("Invalid university response")

        return tuple(rows)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            503,
            "Institution lookup is temporarily unavailable.",
        ) from exc


def search_universities(query: str) -> list[dict[str, Any]]:
    return list(
        _search_universities(
            query,
            int(time.time() // 600),
        )
    )


def resolve_identity(
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    matches = {
        str(row["id"]): row
        for row in search_universities(scorecard["name"])
        if row.get("id") is not None
        and same_institution(scorecard, row)
    }

    if len(matches) != 1:
        raise HTTPException(
            409,
            "We couldn't unambiguously match your institution's "
            "email domains. Check your selected institution, "
            "or use manual verification.",
        )

    return next(iter(matches.values()))


def require_institution_email(
    email: str,
    identity: dict[str, Any],
) -> str:
    email = email.strip().lower()

    # Consistent with AccountEmail and the existing OTP DB constraint.
    if not re.fullmatch(
        r"[a-z0-9._%+-]+@[a-z0-9.-]+\.edu",
        email,
    ):
        raise HTTPException(
            400,
            "Please use a valid .edu email address.",
        )

    domains = identity.get("domains", [])

    if (
        not isinstance(domains, list)
        or not domain_matches(
            email.rsplit("@", 1)[1],
            domains,
        )
    ):
        raise HTTPException(
            400,
            "This email does not match your selected institution.",
        )

    return email


@lru_cache(maxsize=512)
def _get_entity(
    entity_id: str,
    cache_bucket: int,
) -> dict[str, Any]:
    try:
        response = httpx.get(
            STUDID_ENTITY_URL + quote(entity_id, safe=""),
            headers={
                "User-Agent": "SmartCampusAssistant/1.0",
            },
            timeout=15,
            follow_redirects=False,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Invalid entity metadata")

        return data
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            503,
            "Institutional sign-in metadata is unavailable. "
            "Please use email OTP.",
        ) from exc


def entity_matches(
    identity: dict[str, Any],
    entity_id: str,
) -> bool:
    if not isinstance(entity_id, str) or not 1 <= len(entity_id) <= 512:
        return False

    data = _get_entity(entity_id, int(time.time() // 600))

    if data.get("entityID") != entity_id or data.get("type") != "live":
        return False

    country = data.get("country")

    if not isinstance(country, str) or country.upper() not in {"US", "USA"}:
        return False

    scopes = data.get("scopes", [])
    domains = identity.get("domains", [])

    if not isinstance(scopes, list) or not isinstance(domains, list):
        return False

    # scope: the security domain the IdP asserts for its users (e.g. wichita.edu)
    # matching it to the institution's domains is better than comparing organisation names/URLs
    return any(
        isinstance(scope, str) and domain_matches(scope, domains)
        for scope in scopes
    )