"""Tests for the AppWash API client (request shape + error handling)."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from appwash.api import (
    AppWashAPI,
    AppWashAuthError,
    AppWashConnectionError,
    AppWashError,
    AppWashRateLimitError,
)

from fixtures import (
    CYCLES_RESPONSE,
    LOCATION_ID,
    MACHINES_RESPONSE,
    OCCUPIED_MACHINE_ID,
    ORDERS_RESPONSE,
    USER_RESPONSE,
    WALLET_RESPONSE,
)

ACCESS_TOKEN = "test-access-token"
PASSWORD = "sup3r-s3cret"

DEFAULT_ROUTES = {
    "/machines": MACHINES_RESPONSE,
    "/cycles": CYCLES_RESPONSE,
    "/orders": ORDERS_RESPONSE,
    "/user": USER_RESPONSE,
    "/account/wallet": WALLET_RESPONSE,
}


class FakeAPI:
    """A stand-in for the AppWash API that records incoming requests."""

    def __init__(self, routes=None, status=200):
        self.routes = DEFAULT_ROUTES if routes is None else routes
        self.status = status
        self.requests: list[dict] = []
        self.server: TestServer | None = None
        self.session: aiohttp.ClientSession | None = None

    async def _handle(self, request: web.Request) -> web.Response:
        self.requests.append(
            {
                "path": request.path,
                "query": dict(request.query),
                "headers": dict(request.headers),
            }
        )

        if self.status != 200:
            return web.json_response({"error": "nope"}, status=self.status)

        for path, payload in self.routes.items():
            if request.path == path:
                return web.json_response(payload)

        return web.json_response({"error": "not found"}, status=404)

    async def start(self) -> AppWashAPI:
        app = web.Application()
        app.router.add_route("GET", "/{tail:.*}", self._handle)

        self.server = TestServer(app)
        await self.server.start_server()
        self.session = aiohttp.ClientSession()

        api = AppWashAPI("user@example.com", PASSWORD, session=self.session)
        api.BASE_URL = str(self.server.make_url("")).rstrip("/")
        api._access_token = ACCESS_TOKEN
        api._token_expires_at = time.monotonic() + 3600

        return api

    async def stop(self) -> None:
        if self.session is not None:
            await self.session.close()
        if self.server is not None:
            await self.server.close()

    @property
    def paths(self) -> list[str]:
        return [request["path"] for request in self.requests]


@pytest.fixture
async def fake_api():
    """Return a started fake API."""
    fake = FakeAPI()
    api = await fake.start()

    yield fake, api

    await fake.stop()


async def _server(routes=None, status=200):
    fake = FakeAPI(routes, status)
    api = await fake.start()

    return fake, api


# ----------------------------------------------------------------------
# Request shape
# ----------------------------------------------------------------------


async def test_machines_request_uses_location_query(fake_api):
    fake, api = fake_api

    machines = await api.async_get_machines(LOCATION_ID)

    assert fake.paths == ["/machines"]
    assert fake.requests[0]["query"] == {"location.id": LOCATION_ID}
    assert [machine.code for machine in machines] == ["46084", "46115"]


async def test_cycles_request_uses_paging(fake_api):
    fake, api = fake_api

    cycles = await api.async_get_cycles()

    assert fake.paths == ["/cycles"]
    assert fake.requests[0]["query"] == {"page": "0", "size": "20"}
    assert len(cycles) == 2


async def test_cycles_request_can_filter_by_location(fake_api):
    fake, api = fake_api

    await api.async_get_cycles(LOCATION_ID)

    assert fake.requests[0]["query"] == {
        "page": "0",
        "size": "20",
        "location.id": LOCATION_ID,
    }


async def test_orders_request_uses_paging(fake_api):
    fake, api = fake_api

    orders = await api.async_get_orders()

    assert fake.paths == ["/orders"]
    assert fake.requests[0]["query"] == {"page": "0", "size": "20"}
    assert len(orders) == 1


async def test_machine_detail_endpoint(fake_api):
    fake, api = fake_api
    fake.routes = {
        f"/machines/{OCCUPIED_MACHINE_ID}": MACHINES_RESPONSE["items"][0]
    }

    machine = await api.async_get_machine(OCCUPIED_MACHINE_ID)

    assert fake.paths == [f"/machines/{OCCUPIED_MACHINE_ID}"]
    assert machine is not None
    assert machine.code == "46084"


async def test_location_is_resolved_from_the_user_endpoint(fake_api):
    fake, api = fake_api

    location_id = await api.async_get_location_id()

    assert location_id == LOCATION_ID
    assert fake.paths == ["/user"]

    # The resolved location is cached, so no second /user request.
    await api.async_get_machines()

    assert fake.paths == ["/user", "/machines"]


async def test_balance_comes_from_the_wallet_endpoint(fake_api):
    fake, api = fake_api

    balance = await api.async_get_balance()

    assert fake.paths == ["/account/wallet"]
    assert balance == 3.0


async def test_requests_are_authenticated_with_a_bearer_token(fake_api):
    fake, api = fake_api

    await api.async_get_machines(LOCATION_ID)

    assert fake.requests[0]["headers"]["Authorization"] == f"Bearer {ACCESS_TOKEN}"


async def test_client_does_not_use_the_legacy_api():
    """The old involtum endpoints must not be used any more."""
    root = Path(__file__).resolve().parents[1]
    production = [
        path
        for path in root.glob("*.py")
        if path.parent.name != "tests"
    ]

    assert production

    for path in production:
        source = path.read_text()

        assert "involtum-services.com" not in source
        assert "connectorsv2" not in source
        assert "/api-rest" not in source
        assert "getprepaid" not in source


# ----------------------------------------------------------------------
# Error handling
# ----------------------------------------------------------------------


async def test_401_triggers_one_reauthentication_attempt(monkeypatch):
    fake, api = await _server(status=401)

    logins = []

    async def fake_login():
        logins.append(True)
        api._access_token = "refreshed-token"
        api._token_expires_at = time.monotonic() + 3600

    monkeypatch.setattr(api, "_async_login", fake_login)

    try:
        with pytest.raises(AppWashAuthError):
            await api.async_get_machines(LOCATION_ID)

        assert len(logins) == 1
        assert len(fake.requests) == 2
        assert fake.requests[1]["headers"]["Authorization"] == (
            "Bearer refreshed-token"
        )
    finally:
        await fake.stop()


async def test_403_raises_auth_error_without_retry():
    fake, api = await _server(status=403)

    try:
        with pytest.raises(AppWashAuthError):
            await api.async_get_machines(LOCATION_ID)

        assert len(fake.requests) == 1
    finally:
        await fake.stop()


async def test_429_raises_rate_limit_error():
    fake, api = await _server(status=429)

    try:
        with pytest.raises(AppWashRateLimitError):
            await api.async_get_machines(LOCATION_ID)

        assert len(fake.requests) == 1
    finally:
        await fake.stop()


async def test_500_raises_connection_error():
    fake, api = await _server(status=503)

    try:
        with pytest.raises(AppWashConnectionError):
            await api.async_get_machines(LOCATION_ID)
    finally:
        await fake.stop()


async def test_404_raises_generic_error():
    fake, api = await _server(status=404)

    try:
        with pytest.raises(AppWashError):
            await api.async_get_machines(LOCATION_ID)
    finally:
        await fake.stop()


async def test_network_failure_raises_connection_error():
    session = aiohttp.ClientSession()
    api = AppWashAPI("user@example.com", PASSWORD, session=session)
    # Port 1 is closed, so the connection attempt fails immediately.
    api.BASE_URL = "http://127.0.0.1:1"
    api._access_token = ACCESS_TOKEN
    api._token_expires_at = time.monotonic() + 3600

    try:
        with pytest.raises(AppWashConnectionError):
            await api.async_get_machines(LOCATION_ID)
    finally:
        await session.close()


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------


async def test_credentials_are_never_logged(fake_api, caplog):
    fake, api = fake_api

    with caplog.at_level(logging.DEBUG, logger="appwash.api"):
        await api.async_get_machines(LOCATION_ID)
        await api.async_get_cycles(LOCATION_ID)

    text = caplog.text

    assert ACCESS_TOKEN not in text
    assert PASSWORD not in text
    assert "Authorization" not in text
    assert "Bearer" not in text
    # Useful debug output is still produced.
    assert "GET /machines" in text
    assert "Fetched 2 machines" in text


async def test_auth_errors_do_not_contain_credentials():
    fake, api = await _server(status=403)

    try:
        with pytest.raises(AppWashAuthError) as err:
            await api.async_get_machines(LOCATION_ID)

        assert PASSWORD not in str(err.value)
        assert ACCESS_TOKEN not in str(err.value)
    finally:
        await fake.stop()
