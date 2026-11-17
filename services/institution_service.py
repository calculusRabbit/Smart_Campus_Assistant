# College Scorecard institution and program selection

import os
from functools import lru_cache
from typing import Any

import httpx
from fastapi import HTTPException

BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

US_STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA "
    "MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN "
    "TX UT VT VA WA WV WI WY DC"
)


def _get(**params: Any) -> list[dict[str, Any]]:
    key = os.environ.get("SCORECARD_API_KEY")
    if not key:
        raise HTTPException(503, "Institution search is not configured")

    try:
        response = httpx.get(
            BASE_URL, params={"api_key": key, "keys_nested": "true", **params}, timeout=15
        )
        response.raise_for_status()
        results: list[dict[str, Any]] = response.json()["results"]
        return results
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(
            503, "Institution search is unavailable, please try again later."
        ) from exc


def search_institutions(query: str) -> list[dict[str, Any]]:
    rows = _get(
        **{
            "school.name": query,
            "school.state": ",".join(US_STATES.split()),
            "fields": "id,school.name,school.city,school.state",
            "per_page": 20,
        }
    )

    return [{"id": row["id"], **row["school"]} for row in rows]


@lru_cache(maxsize=256)
def get_institution(scorecard_id: int) -> dict[str, Any]:
    rows = _get(
        **{
            "id": scorecard_id,
            "fields": ("id,school.name,school.city,school.state,latest.programs.cip_4_digit"),
            "all_programs_nested": "true",
        }
    )

    if not rows:
        raise HTTPException(400, "Choose an institution from the search results")

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
