import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_hits: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(max_requests: int, window_seconds: int = 60):
    """Fixed-window rate limit dependency, keyed by client IP + route path.

    In-memory only - resets on process restart and doesn't coordinate across
    multiple worker processes. Fine for this app's single-instance deployment;
    swap for a Redis-backed limiter if that changes.
    """

    async def dependency(request: Request) -> None:
        key = f"{_client_key(request)}:{request.url.path}"
        now = time.monotonic()
        hits = _hits[key]
        cutoff = now - window_seconds
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= max_requests:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please try again later.",
            )
        hits.append(now)

    return dependency
