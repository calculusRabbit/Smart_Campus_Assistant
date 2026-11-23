import os
from typing import Any

import httpx
from fastapi import HTTPException

from services.institution_identity import resolve_identity, same_institution, search_universities

BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

US_STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA "
    "MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN "
    "TX UT VT VA WA WV WI WY DC"
)


def _get(**params: Any) -> list[dict[str, Any]]:
    key = os.environ.get("SCORECARD_API_KEY")

    if not key:
        raise HTTPException(
            503,
            "Institution search is not configured",
        )

    try:
        response = httpx.get(
            BASE_URL,
            params={
                "api_key": key,
                "keys_nested": "true",
                **params,
            },
            timeout=15,
        )
        response.raise_for_status()
        results = response.json()["results"]

        if not isinstance(results, list) or any(not isinstance(row, dict) for row in results):
            raise ValueError("Invalid Scorecard response")

        return results
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(
            503,
            "Institution search is unavailable, please try again later.",
        ) from exc


def _search_scorecard(query: str) -> list[dict[str, Any]]:
    rows = _get(
        **{
            "school.name": query,
            "school.state": ",".join(US_STATES.split()),
            "fields": ("id,school.name,school.city,school.state,school.school_url"),
            "per_page": 20,
        }
    )

    return [{"id": row["id"], **row["school"]} for row in rows]


def _enrichment(identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "native_name": identity.get("native_name"),
        "acronym": identity.get("acronym"),
        "aliases": identity.get("aliases", []),
    }


def search_institutions(query: str) -> list[dict[str, Any]]:
    rows = _search_scorecard(query)

    try:
        candidates = search_universities(query)
    except HTTPException:
        # in case of enrichment outage: search is available, verification isn't
        return rows

    # searching with an alias might not match the Scorecard name
    if not rows:
        for candidate in candidates[:3]:
            name = candidate.get("name")

            if not isinstance(name, str):
                continue

            for row in _search_scorecard(name):
                if same_institution(row, candidate):
                    rows.append(row)

    results = {}

    for row in rows:
        matches = [item for item in candidates if same_institution(row, item)]

        if len(matches) == 1:
            row = {
                **row,
                **_enrichment(matches[0]),
            }

        results[row["id"]] = row

    return list(results.values())[:20]


def get_institution(scorecard_id: int) -> dict[str, Any]:
    rows = _get(
        **{
            "id": scorecard_id,
            "fields": (
                "id,school.name,school.city,school.state,"
                "school.school_url,latest.programs.cip_4_digit"
            ),
            "all_programs_nested": "true",
        }
    )

    if not rows:
        raise HTTPException(
            400,
            "Choose an institution from the search results",
        )

    row = rows[0]
    school = row["school"]

    if school.get("state") not in US_STATES.split():
        raise HTTPException(400, "Choose a US institution")

    programs = row.get("latest", {}).get("programs", {}).get("cip_4_digit") or []

    options = {}

    for program in programs:
        code = str(program.get("code", ""))
        title = program.get("title")
        credential = program.get("credential") or {}

        if not code or not title:
            continue

        value = f"{code}:{credential.get('level', '')}"
        label = title

        if credential.get("title"):
            label += f" — {credential['title']}"

        options[value] = {
            "value": value,
            "label": label,
        }

    return {
        "id": row["id"],
        **school,
        "programs": sorted(
            options.values(),
            key=lambda item: item["label"],
        ),
    }


def get_enriched_institution(
    scorecard_id: int,
) -> dict[str, Any]:
    school = get_institution(scorecard_id)

    try:
        identity = resolve_identity(school)
    except HTTPException:
        return school

    return {
        **school,
        **_enrichment(identity),
    }
