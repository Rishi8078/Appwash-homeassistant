"""Tests for the Cognito authentication flow."""
from __future__ import annotations

import logging
import time
from urllib.parse import urlencode

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from appwash import api as api_module
from appwash.api import AppWashAPI, AppWashAuthError, AppWashConnectionError

EMAIL = "user@example.com"
PASSWORD = "sup3r-s3cret"

LOGIN_PAGE = """
<html><body>
  <form name="cognitoSignInForm" action="/login?client_id=abc" method="post">
    <input type="hidden" name="_csrf" value="page-csrf"/>
    <input type="text" name="username" value=""/>
    <input type="submit" name="signInSubmitButton" value="Next"/>
  </form>
</body></html>
"""

PASSWORD_PAGE = """
<html><body>
  <form name="cognitoSignInForm" action="/verifyPassword" method="post">
    <input type="hidden" name="csrf" value="form-csrf"/>
    <input type="hidden" name="cognitoAsfData" value="asf-data"/>
    <input type="password" name="password" value=""/>
  </form>
</body></html>
"""


class FakeCognito:
    """A very small stand-in for the Cognito hosted UI."""

    def __init__(self, valid_password: str = PASSWORD):
        self.valid_password = valid_password
        self.reject_refresh = False
        self.requests: list[dict] = []
        self.server: TestServer | None = None

    async def _authorize(self, request: web.Request) -> web.Response:
        self.requests.append({"path": request.path, "query": dict(request.query)})

        return web.Response(text=LOGIN_PAGE, content_type="text/html")

    async def _login(self, request: web.Request) -> web.Response:
        form = dict(await request.post())
        self.requests.append({"path": request.path, "form": form})

        return web.Response(text=PASSWORD_PAGE, content_type="text/html")

    async def _verify_password(self, request: web.Request) -> web.Response:
        form = dict(await request.post())
        self.requests.append(
            {"path": request.path, "form": form, "query": dict(request.query)}
        )

        if form.get("password") != f'"{self.valid_password}"':
            return web.Response(text="wrong password", content_type="text/html")

        query = urlencode(
            {"code": "auth-code", "state": request.query.get("state", "")}
        )

        return web.Response(
            status=302,
            headers={"Location": f"https://web.appwash.com/auth-callback?{query}"},
        )

    async def _token(self, request: web.Request) -> web.Response:
        form = dict(await request.post())
        self.requests.append({"path": request.path, "form": form})

        if self.reject_refresh and form.get("grant_type") == "refresh_token":
            return web.json_response({"error": "invalid_grant"}, status=400)

        return web.json_response(
            {
                "access_token": f"access-for-{form.get('grant_type')}",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
        )

    async def start(self) -> str:
        app = web.Application()
        app.router.add_get("/oauth2/authorize", self._authorize)
        app.router.add_post("/login", self._login)
        app.router.add_post("/verifyPassword", self._verify_password)
        app.router.add_post("/oauth2/token", self._token)

        self.server = TestServer(app)
        await self.server.start_server()

        return str(self.server.make_url("")).rstrip("/")

    async def stop(self) -> None:
        if self.server is not None:
            await self.server.close()

    @property
    def paths(self) -> list[str]:
        return [request["path"] for request in self.requests]


@pytest.fixture
async def cognito(monkeypatch):
    """Point the client at a fake Cognito and yield it."""
    fake = FakeCognito()
    url = await fake.start()
    monkeypatch.setattr(api_module, "COGNITO_URL", url)

    yield fake

    await fake.stop()


async def test_login_walks_the_hosted_ui_and_stores_tokens(cognito):
    api = AppWashAPI(EMAIL, PASSWORD)

    await api.async_login()

    assert cognito.paths == [
        "/oauth2/authorize",
        "/login",
        "/verifyPassword",
        "/oauth2/token",
    ]

    authorize = cognito.requests[0]["query"]

    assert authorize["client_id"] == api_module.COGNITO_CLIENT_ID
    assert authorize["response_type"] == "code"
    assert authorize["code_challenge_method"] == "S256"
    assert authorize["code_challenge"]

    # The hosted UI expects JSON-encoded form values.
    assert cognito.requests[1]["form"]["username"] == f'"{EMAIL}"'
    assert cognito.requests[2]["form"]["csrf"] == '"form-csrf"'
    assert cognito.requests[2]["form"]["cognitoAsfData"] == "asf-data"

    token_request = cognito.requests[3]["form"]

    assert token_request["grant_type"] == "authorization_code"
    assert token_request["code"] == "auth-code"
    assert token_request["code_verifier"]

    assert api._access_token == "access-for-authorization_code"
    assert api._refresh_token == "refresh-token"
    assert api._token_expires_at > time.monotonic()

    await api.close()


async def test_login_with_wrong_password_raises_auth_error(cognito):
    api = AppWashAPI(EMAIL, "wrong-password")

    with pytest.raises(AppWashAuthError):
        await api.async_login()

    await api.close()


async def test_expired_token_is_refreshed(cognito):
    api = AppWashAPI(EMAIL, PASSWORD)
    api._access_token = "old-token"
    api._refresh_token = "refresh-token"
    api._token_expires_at = time.monotonic() - 1

    await api._async_ensure_token()

    assert cognito.paths == ["/oauth2/token"]
    assert cognito.requests[0]["form"]["grant_type"] == "refresh_token"
    assert api._access_token == "access-for-refresh_token"

    await api.close()


async def test_rejected_refresh_token_falls_back_to_a_full_login(cognito):
    cognito.reject_refresh = True

    api = AppWashAPI(EMAIL, PASSWORD)
    api._access_token = "old-token"
    api._refresh_token = "stale-refresh-token"
    api._token_expires_at = time.monotonic() - 1

    await api._async_ensure_token()

    # The stale refresh token is dropped and the hosted UI login runs again.
    assert cognito.paths[0] == "/oauth2/token"
    assert "/oauth2/authorize" in cognito.paths
    assert api._access_token == "access-for-authorization_code"

    await api.close()


async def test_authentication_never_logs_credentials(cognito, caplog):
    api = AppWashAPI(EMAIL, PASSWORD)

    with caplog.at_level(logging.DEBUG, logger="appwash.api"):
        await api.async_login()

    assert PASSWORD not in caplog.text
    assert api._access_token not in caplog.text
    assert "refresh-token" not in caplog.text

    await api.close()


async def test_unreachable_cognito_raises_connection_error(monkeypatch):
    monkeypatch.setattr(api_module, "COGNITO_URL", "http://127.0.0.1:1")

    api = AppWashAPI(EMAIL, PASSWORD)

    with pytest.raises(AppWashConnectionError):
        await api.async_login()

    await api.close()
