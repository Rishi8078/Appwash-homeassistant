"""API client for AppWash (Miele MOVE).

Authentication uses the Amazon Cognito hosted UI (OAuth 2.0 authorization
code flow with PKCE) that the current AppWash web application uses.  All
data requests go to ``https://www.miele-move.com/appwash/api/app/v1`` and
are read-only.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import secrets
import time
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import aiohttp

from .const import (
    API_BASE_URL,
    APP_HEADER,
    COGNITO_CLIENT_ID,
    COGNITO_REDIRECT_URI,
    COGNITO_SCOPE,
    COGNITO_URL,
    REQUEST_TIMEOUT,
    WEB_ORIGIN,
)
from .models import Cycle, Machine, parse_cycles, parse_machines

_LOGGER = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0"
)

# Refresh a little before the token actually expires.
_TOKEN_EXPIRY_MARGIN = 60


class AppWashError(Exception):
    """Base error for the AppWash API."""


class AppWashAuthError(AppWashError):
    """Authentication failed or the account is not allowed to see a resource."""


class AppWashRateLimitError(AppWashError):
    """The API answered with HTTP 429."""


class AppWashConnectionError(AppWashError):
    """The API could not be reached or answered with a server error."""


class _FormParser(HTMLParser):
    """Minimal HTML form scraper for the Cognito hosted login pages."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, Any]] = []
        self._current: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: (value or "") for key, value in attrs}

        if tag == "form":
            self._current = {
                "action": attributes.get("action", ""),
                "fields": {},
            }
            return

        if tag != "input" or self._current is None:
            return

        name = attributes.get("name")

        if not name or attributes.get("type", "text") in ("submit", "button"):
            return

        self._current["fields"][name] = attributes.get("value", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._current is not None:
            self.forms.append(self._current)
            self._current = None

    def find_form(self, field: str) -> dict[str, Any] | None:
        """Return the first form containing ``field``."""
        for form in self.forms:
            if field in form["fields"]:
                return form

        return None


def _make_pkce() -> tuple[str, str]:
    """Return a PKCE (verifier, challenge) pair."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    return verifier, challenge


class AppWashAPI:
    """AppWash API client."""

    BASE_URL = API_BASE_URL

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        location_id: str | None = None,
    ) -> None:
        """Initialize the API client.

        ``session`` may be Home Assistant's shared client session.  When it is
        omitted the client owns (and closes) its own session.
        """
        self._email = email
        self._password = password
        self._session = session
        self._owns_session = session is None
        self._location_id = location_id
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0.0
        self._auth_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    @property
    def location_id(self) -> str | None:
        """Return the location the client is bound to, if known."""
        return self._location_id

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the session used for API calls."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

        return self._session

    async def close(self) -> None:
        """Close the session if this client owns it."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def async_login(self) -> None:
        """Authenticate against Cognito and store the resulting tokens."""
        async with self._auth_lock:
            await self._async_login()

    async def _async_login(self) -> None:
        """Run the Cognito hosted-UI login (assumes the auth lock is held)."""
        verifier, challenge = _make_pkce()
        state = secrets.token_urlsafe(16)

        oauth = {
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "lang": "en",
            "prompt": "select_account",
            "redirect_uri": COGNITO_REDIRECT_URI,
            "client_id": COGNITO_CLIENT_ID,
            "response_type": "code",
            "scope": COGNITO_SCOPE,
            "state": state,
        }

        headers = {
            "User-Agent": _USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }

        # The hosted UI is cookie driven; keep those cookies out of the
        # shared Home Assistant session.
        login_session = aiohttp.ClientSession(headers=headers)

        try:
            code = await self._async_authorization_code(
                login_session, oauth, state
            )
            await self._async_exchange_code(login_session, code, verifier)
        finally:
            await login_session.close()

        _LOGGER.debug("AppWash authentication successful")

    async def _async_authorization_code(
        self,
        session: aiohttp.ClientSession,
        oauth: dict[str, str],
        state: str,
    ) -> str:
        """Walk the hosted UI username/password forms and return the code."""
        authorize_url = f"{COGNITO_URL}/oauth2/authorize?{urlencode(oauth)}"

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.get(authorize_url) as response:
                    if response.status >= 400:
                        raise AppWashAuthError(
                            "Cognito authorization page returned HTTP "
                            f"{response.status}"
                        )

                    page = await response.text()
                    page_url = str(response.url)

            parser = _FormParser()
            parser.feed(page)
            username_form = parser.find_form("username")

            if username_form is None:
                raise AppWashAuthError("Cognito username form not found")

            fields = dict(username_form["fields"])
            # The hosted UI expects JSON-encoded (quoted) values.
            fields["username"] = json.dumps(self._email)
            username_url = urljoin(page_url, username_form["action"] or page_url)

            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.post(username_url, data=fields) as response:
                    if response.status >= 400:
                        raise AppWashAuthError(
                            f"Cognito username step returned HTTP {response.status}"
                        )

                    page = await response.text()
                    referer = str(response.url)

            parser = _FormParser()
            parser.feed(page)

            csrf = None
            cognito_asf = None

            for form in parser.forms:
                csrf = form["fields"].get("csrf") or csrf
                cognito_asf = form["fields"].get("cognitoAsfData") or cognito_asf

            if not csrf:
                for cookie in session.cookie_jar:
                    if cookie.key == "XSRF-TOKEN":
                        csrf = cookie.value
                        break

            if not csrf:
                raise AppWashAuthError("Cognito CSRF token not found")

            data = {
                "password": json.dumps(self._password),
                "csrf": json.dumps(csrf),
            }

            if cognito_asf:
                data["cognitoAsfData"] = cognito_asf

            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.post(
                    f"{COGNITO_URL}/verifyPassword",
                    params=oauth,
                    data=data,
                    headers={
                        "Content-Type": (
                            "application/x-www-form-urlencoded;charset=UTF-8"
                        ),
                        "Origin": COGNITO_URL,
                        "Referer": referer,
                        "Accept": "*/*",
                    },
                    allow_redirects=False,
                ) as response:
                    callback = response.headers.get("Location")

        except asyncio.TimeoutError as err:
            raise AppWashConnectionError("Timeout during authentication") from err
        except aiohttp.ClientError as err:
            raise AppWashConnectionError(
                f"Connection error during authentication: {err}"
            ) from err

        if not callback:
            raise AppWashAuthError("Invalid credentials or unexpected login flow")

        query = parse_qs(urlparse(urljoin(COGNITO_URL, callback)).query)

        if query.get("state", [None])[0] != state:
            raise AppWashAuthError("OAuth state mismatch")

        code = query.get("code", [None])[0]

        if not code:
            raise AppWashAuthError(
                "Cognito returned no authorization code: "
                f"{query.get('error', ['unknown'])[0]}"
            )

        return code

    async def _async_exchange_code(
        self,
        session: aiohttp.ClientSession,
        code: str,
        verifier: str,
    ) -> None:
        """Exchange an authorization code for tokens."""
        await self._async_token_request(
            session,
            {
                "grant_type": "authorization_code",
                "client_id": COGNITO_CLIENT_ID,
                "code_verifier": verifier,
                "redirect_uri": COGNITO_REDIRECT_URI,
                "code": code,
            },
        )

    async def _async_token_request(
        self,
        session: aiohttp.ClientSession,
        data: dict[str, str],
    ) -> None:
        """Call the Cognito token endpoint and store the result."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.post(
                    f"{COGNITO_URL}/oauth2/token",
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                ) as response:
                    if response.status in (400, 401):
                        raise AppWashAuthError(
                            f"Token request rejected (HTTP {response.status})"
                        )

                    if response.status != 200:
                        raise AppWashConnectionError(
                            f"Token request failed (HTTP {response.status})"
                        )

                    payload = await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise AppWashConnectionError("Timeout during token request") from err
        except aiohttp.ClientError as err:
            raise AppWashConnectionError(f"Token request failed: {err}") from err

        token = payload.get("access_token") if isinstance(payload, dict) else None

        if not token:
            raise AppWashAuthError("No access token in Cognito response")

        self._access_token = token
        self._refresh_token = payload.get("refresh_token") or self._refresh_token
        self._token_expires_at = time.monotonic() + float(
            payload.get("expires_in") or 3600
        )

    async def _async_refresh(self) -> None:
        """Refresh the access token, falling back to a full login."""
        if not self._refresh_token:
            await self._async_login()
            return

        session = aiohttp.ClientSession(headers={"User-Agent": _USER_AGENT})

        try:
            await self._async_token_request(
                session,
                {
                    "grant_type": "refresh_token",
                    "client_id": COGNITO_CLIENT_ID,
                    "refresh_token": self._refresh_token,
                },
            )
        except AppWashAuthError:
            _LOGGER.debug("Refresh token rejected, performing a full login")
            self._refresh_token = None
            await self._async_login()
        finally:
            await session.close()

    async def _async_ensure_token(self, force: bool = False) -> None:
        """Make sure a usable access token is available."""
        async with self._auth_lock:
            if force:
                await self._async_refresh()
                return

            if self._access_token is None:
                await self._async_login()
                return

            if time.monotonic() >= self._token_expires_at - _TOKEN_EXPIRY_MARGIN:
                await self._async_refresh()

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Appwash-App": APP_HEADER,
            "Origin": WEB_ORIGIN,
            "Referer": f"{WEB_ORIGIN}/",
            "User-Agent": _USER_AGENT,
        }

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    async def _async_request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Perform an authenticated GET request against the AppWash API."""
        await self._async_ensure_token()

        url = f"{self.BASE_URL}{path}"
        session = self._get_session()

        _LOGGER.debug("GET %s params=%s", path, params)

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                ) as response:
                    status = response.status

                    if status == 401 and retry_auth:
                        _LOGGER.debug("Token rejected, re-authenticating")
                        await self._async_ensure_token(force=True)
                        return await self._async_request(
                            path, params, retry_auth=False
                        )

                    if status == 401:
                        raise AppWashAuthError(
                            f"Not authenticated for {path} (HTTP 401)"
                        )

                    if status == 403:
                        raise AppWashAuthError(
                            f"Access denied for {path} (HTTP 403)"
                        )

                    if status == 429:
                        raise AppWashRateLimitError(
                            f"Rate limited by the AppWash API on {path}"
                        )

                    if status >= 500:
                        raise AppWashConnectionError(
                            f"AppWash API error on {path} (HTTP {status})"
                        )

                    if status >= 400:
                        raise AppWashError(
                            f"Unexpected response for {path} (HTTP {status})"
                        )

                    return await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise AppWashConnectionError(f"Timeout while requesting {path}") from err
        except aiohttp.ClientError as err:
            raise AppWashConnectionError(
                f"Connection error while requesting {path}: {err}"
            ) from err

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    async def async_get_user(self) -> dict[str, Any]:
        """Return the current user (``GET /user``)."""
        return await self._async_request("/user")

    async def async_get_location(self, location_id: str) -> dict[str, Any]:
        """Return a location (``GET /locations/{id}``)."""
        return await self._async_request(f"/locations/{location_id}")

    async def _async_get_location(self) -> None:
        """Resolve and cache the location id of the account."""
        user = await self.async_get_user()
        preferred = user.get("preferredLocation") or {}
        location_id = preferred.get("id")

        if not location_id:
            raise AppWashError(
                "No preferred location on the AppWash account; "
                "configure a location id in the integration options"
            )

        self._location_id = location_id
        _LOGGER.debug("Resolved AppWash location %s", location_id)

    async def async_get_location_id(self) -> str:
        """Return the location id, resolving it from the account if needed."""
        if not self._location_id:
            await self._async_get_location()

        return self._location_id

    async def async_get_machines(
        self, location_id: str | None = None
    ) -> list[Machine]:
        """Return all machines of a location.

        Uses the collection endpoint so a single request covers every entity.
        """
        location = location_id or await self.async_get_location_id()

        payload = await self._async_request(
            "/machines", {"location.id": location}
        )
        machines = parse_machines(payload)

        _LOGGER.debug(
            "Fetched %s machines: %s",
            len(machines),
            {machine.code: machine.availability_status for machine in machines},
        )

        return machines

    async def async_get_machine(self, machine_id: str) -> Machine | None:
        """Return a single machine (``GET /machines/{id}``)."""
        payload = await self._async_request(f"/machines/{machine_id}")

        if not isinstance(payload, dict) or not payload.get("id"):
            return None

        return Machine.from_api(payload)

    async def async_get_cycles(
        self,
        location_id: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> list[Cycle]:
        """Return recent cycles (``GET /cycles``)."""
        params: dict[str, Any] = {"page": str(page), "size": str(size)}

        if location_id:
            params["location.id"] = location_id

        cycles = parse_cycles(await self._async_request("/cycles", params))

        _LOGGER.debug(
            "Fetched %s cycles, %s active",
            len(cycles),
            sum(1 for cycle in cycles if cycle.is_active),
        )

        return cycles

    async def async_get_orders(
        self, page: int = 0, size: int = 20
    ) -> list[dict[str, Any]]:
        """Return orders (``GET /orders``).

        Not used during normal polling; machine availability and cycles are
        enough to describe the current state.
        """
        payload = await self._async_request(
            "/orders", {"page": str(page), "size": str(size)}
        )

        return payload.get("items", []) if isinstance(payload, dict) else []

    async def async_get_order(self, order_id: str) -> dict[str, Any]:
        """Return a single order (``GET /orders/{id}``)."""
        return await self._async_request(f"/orders/{order_id}")

    async def async_get_wallet(self) -> dict[str, Any]:
        """Return the wallet (``GET /account/wallet``)."""
        return await self._async_request("/account/wallet")

    async def async_get_balance(self) -> float:
        """Get account balance."""
        wallet = await self.async_get_wallet()

        return float(wallet.get("balance") or 0.0)
