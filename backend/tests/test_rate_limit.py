from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.services import rate_limit as rate_limit_module
from app.services.rate_limit import rate_limit


def _make_client(path: str, max_requests: int) -> TestClient:
    app = FastAPI()

    @app.get(path, dependencies=[Depends(rate_limit(max_requests, 60))])
    def endpoint():
        return {"ok": True}

    return TestClient(app)


def setup_function():
    # Module-level hit-tracking dict persists across tests in the same
    # process; clear it so tests don't leak state into one another.
    rate_limit_module._hits.clear()


def test_allows_requests_under_the_limit():
    client = _make_client("/under-limit", max_requests=3)

    for _ in range(3):
        assert client.get("/under-limit").status_code == 200


def test_blocks_requests_once_limit_is_exceeded():
    client = _make_client("/over-limit", max_requests=3)

    for _ in range(3):
        assert client.get("/over-limit").status_code == 200

    response = client.get("/over-limit")
    assert response.status_code == 429


def test_limit_is_scoped_per_route_path():
    app = FastAPI()

    @app.get("/route-a", dependencies=[Depends(rate_limit(1, 60))])
    def route_a():
        return {"ok": True}

    @app.get("/route-b", dependencies=[Depends(rate_limit(1, 60))])
    def route_b():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/route-a").status_code == 200
    assert client.get("/route-a").status_code == 429
    # A different route for the same client should have its own budget.
    assert client.get("/route-b").status_code == 200
