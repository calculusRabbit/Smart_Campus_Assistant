import time
from collections import deque

from fastapi import HTTPException, Request

SEARCH_LIMIT = 20
SEARCH_WINDOW_SECONDS = 60
_search_hits: dict[str, deque[float]] = {}


def limit_institution_search(request: Request) -> None:
    # per-client cap (each uncached search takes up some of API quota)
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    hits = _search_hits.setdefault(client, deque())

    while hits and now - hits[0] > SEARCH_WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= SEARCH_LIMIT:
        raise HTTPException(
            429,
            "Too many institution searches. Wait a minute and try again.",
            headers={"Retry-After": str(SEARCH_WINDOW_SECONDS)},
        )

    hits.append(now)

    # drop idle clients so the dict can't grow without bound
    if len(_search_hits) > 10_000:
        idle = [
            key
            for key, value in _search_hits.items()
            if not value or now - value[-1] > SEARCH_WINDOW_SECONDS
        ]

        for key in idle:
            del _search_hits[key]