#!/usr/bin/env python3
"""
AppWash API Finder v2

Read-only API mapper for the current AppWash web API.

What it does:
  1. Logs in through the current Cognito web flow.
  2. Verifies authentication against a known-good API endpoint.
  3. Collects IDs returned by the API for this account/location.
  4. Tests confirmed detail endpoints using those real IDs.
  5. Tests a small set of query parameters suggested by observed schemas.
  6. Tests a small set of relationship routes.
  7. Checks authenticated Swagger/OpenAPI locations.
  8. Writes JSON + Markdown reports.

Safety:
  - AppWash API requests are GET only.
  - No POST/PUT/PATCH/DELETE.
  - No random UUID enumeration.
  - No large wordlist/path brute force.
  - Stops on rate limiting.
"""

import base64
import hashlib
import json
import os
import secrets
import sys
import time
from datetime import datetime
from urllib.parse import urlencode, urljoin, urlparse, parse_qs, quote

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COGNITO_HOST = "https://appwash.auth.eu-north-1.amazoncognito.com"
CLIENT_ID = "24n99a16tg55iaclg2frjrma32"
REDIRECT_URI = "https://web.appwash.com/auth-callback"

HOST = "https://www.miele-move.com"
API_BASE = f"{HOST}/appwash/api/app/v1"

APP_HEADER = "web/3.4.0"

EMAIL = os.getenv("APPWASH_EMAIL")
PASSWORD = os.getenv("APPWASH_PASSWORD")
LOCATION_ID_ENV = os.getenv("APPWASH_LOCATION_ID")

OUTPUT_JSON = os.getenv(
    "APPWASH_FINDER_V2_OUTPUT",
    "v2_results.json",
)
OUTPUT_MD = os.getenv(
    "APPWASH_FINDER_V2_REPORT",
    "v2_report.md",
)

try:
    REQUEST_DELAY = max(
        0.25,
        float(os.getenv("APPWASH_FINDER_V2_DELAY", "0.4")),
    )
except ValueError:
    REQUEST_DELAY = 0.4

MAX_MACHINE_DETAILS = 3
MAX_CYCLE_DETAILS = 3
MAX_ORDER_DETAILS = 3
MAX_ORDER_ITEM_DETAILS = 3
MAX_RESERVATION_DETAILS = 3

RATE_LIMITED = False


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def die(message):
    print(f"\nERROR: {message}")
    sys.exit(1)


def safe_json(response):
    try:
        return response.json()
    except ValueError:
        return response.text[:12000]


def jvalue(value):
    return json.dumps(value)


def make_pkce():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def form_fields(form):
    fields = {}

    for element in form.find_all("input"):
        name = element.get("name")

        if not name:
            continue

        if element.get("type", "text") in {"submit", "button"}:
            continue

        fields[name] = element.get("value", "")

    return fields


def unique(values):
    return list(dict.fromkeys(
        x for x in values
        if x not in (None, "")
    ))


def extract_items(body):
    """
    Current AppWash collection responses use:
        {"items": [...]}

    Also tolerate nested structures in case an endpoint differs.
    """
    if not isinstance(body, dict):
        return []

    if isinstance(body.get("items"), list):
        return body["items"]

    for key in ("data", "results", "content"):
        value = body.get(key)

        if isinstance(value, dict) and isinstance(value.get("items"), list):
            return value["items"]

        if isinstance(value, list):
            return value

    return []


def extract_id(obj):
    return obj.get("id") if isinstance(obj, dict) else None


# ---------------------------------------------------------------------------
# Cognito
# ---------------------------------------------------------------------------

def cognito_login():
    if not EMAIL:
        die("APPWASH_EMAIL is missing from .env")

    if not PASSWORD:
        die("APPWASH_PASSWORD is missing from .env")

    verifier, challenge = make_pkce()
    state = secrets.token_urlsafe(16)

    oauth = {
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "lang": "en",
        "prompt": "select_account",
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid email phone profile aws.cognito.signin.user.admin",
        "state": state,
    }

    authorize_url = (
        f"{COGNITO_HOST}/oauth2/authorize?"
        f"{urlencode(oauth)}"
    )

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:153.0) "
            "Gecko/20100101 Firefox/153.0"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })

    print("\n" + "=" * 78)
    print("COGNITO AUTHENTICATION")
    print("=" * 78)

    response = session.get(
        authorize_url,
        timeout=30,
        allow_redirects=True,
    )

    if response.status_code >= 400:
        die(
            f"Cognito authorization failed: "
            f"HTTP {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")

    username_form = None

    for form in soup.find_all("form"):
        names = {
            x.get("name")
            for x in form.find_all("input")
            if x.get("name")
        }

        if "username" in names:
            username_form = form
            break

    if username_form is None:
        die("Cognito username form not found")

    username_url = urljoin(
        response.url,
        username_form.get("action") or response.url,
    )

    fields = form_fields(username_form)
    fields["username"] = jvalue(EMAIL)

    print("Submitting username...")

    response = session.post(
        username_url,
        data=fields,
        timeout=30,
        allow_redirects=True,
    )

    if response.status_code >= 400:
        die(
            f"Cognito username step failed: "
            f"HTTP {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")

    csrf = None
    cognito_asf = None

    for element in soup.find_all("input"):
        name = element.get("name")
        value = element.get("value", "")

        if name == "csrf":
            csrf = value

        elif name == "cognitoAsfData":
            cognito_asf = value

    if not csrf:
        csrf = session.cookies.get("XSRF-TOKEN")

    if not csrf:
        die("Cognito CSRF token not found")

    password_data = {
        "password": jvalue(PASSWORD),
        "csrf": jvalue(csrf),
    }

    if cognito_asf:
        password_data["cognitoAsfData"] = cognito_asf

    print("Submitting password...")

    response = session.post(
        f"{COGNITO_HOST}/verifyPassword",
        params=oauth,
        data=password_data,
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded;charset=UTF-8"
            ),
            "Origin": COGNITO_HOST,
            "Referer": response.url,
            "Accept": "*/*",
        },
        timeout=30,
        allow_redirects=False,
    )

    callback = response.headers.get("Location")

    if not callback:
        die(
            "Cognito password verification did not return "
            "an OAuth callback"
        )

    callback_url = urljoin(
        COGNITO_HOST,
        callback,
    )

    query = parse_qs(urlparse(callback_url).query)

    returned_state = query.get("state", [None])[0]

    if returned_state != state:
        die("OAuth state mismatch")

    code = query.get("code", [None])[0]

    if not code:
        error = query.get("error", ["unknown"])[0]
        description = query.get(
            "error_description",
            [""],
        )[0]

        die(
            f"Cognito returned no authorization code: "
            f"{error} {description}"
        )

    print("Authorization code received.")

    token_response = session.post(
        f"{COGNITO_HOST}/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code_verifier": verifier,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        timeout=30,
    )

    if token_response.status_code != 200:
        die(
            f"Token exchange failed: "
            f"HTTP {token_response.status_code}"
        )

    token = token_response.json().get("access_token")

    if not token:
        die("No access_token in Cognito response")

    print("Authentication successful.")

    return token


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class API:
    def __init__(self, token):
        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/plain, */*",
            "X-Appwash-App": APP_HEADER,
            "Origin": "https://web.appwash.com",
            "Referer": "https://web.appwash.com/",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:153.0) "
                "Gecko/20100101 Firefox/153.0"
            ),
        })

        self.results = []

    def get(self, path_or_url, label, category, params=None):
        global RATE_LIMITED

        if RATE_LIMITED:
            return None

        time.sleep(REQUEST_DELAY)

        if path_or_url.startswith("http"):
            url = path_or_url
        else:
            url = API_BASE + path_or_url

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=25,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            entry = {
                "label": label,
                "category": category,
                "method": "GET",
                "url": url,
                "status": None,
                "error": str(exc),
            }

            self.results.append(entry)

            print(f"[ERR] {label}: {exc}")

            return entry

        body = safe_json(response)

        entry = {
            "label": label,
            "category": category,
            "method": "GET",
            "url": response.url,
            "status": response.status_code,
            "content_type": response.headers.get(
                "Content-Type",
                "",
            ),
            "content_length": response.headers.get(
                "Content-Length"
            ),
            "allow": response.headers.get("Allow"),
            "body": body,
        }

        self.results.append(entry)

        if response.status_code == 429:
            RATE_LIMITED = True
            print("\nRATE LIMIT DETECTED. Stopping discovery.")

        marker = (
            "FOUND"
            if 200 <= response.status_code < 300
            else "----"
        )

        print(
            f"[{marker}] "
            f"{response.status_code:3} "
            f"{label:48} "
            f"{response.url}"
        )

        return entry


# ---------------------------------------------------------------------------
# Known endpoints
# ---------------------------------------------------------------------------

def collect_known(api):
    print("\n" + "=" * 78)
    print("KNOWN API RESOURCES")
    print("=" * 78)

    results = {}

    results["config_well_known"] = api.get(
        "/config/well-known",
        "Config / well-known",
        "known",
    )

    results["config_countries"] = api.get(
        "/config/countries",
        "Config / countries",
        "known",
    )

    results["config_topups"] = api.get(
        "/config/topups",
        "Config / topups",
        "known",
        {"currency": "EUR"},
    )

    results["user"] = api.get(
        "/user",
        "Current user",
        "known",
    )

    location_id = LOCATION_ID_ENV

    try:
        preferred = (
            results["user"]["body"]
            .get("preferredLocation")
            or {}
        )
        location_id = location_id or preferred.get("id")
    except (AttributeError, TypeError):
        pass

    if not location_id:
        die("Could not determine location ID")

    results["location"] = api.get(
        f"/locations/{quote(str(location_id), safe='')}",
        "Location detail",
        "known",
    )

    results["machines"] = api.get(
        "/machines",
        "Machines by location",
        "known",
        {"location.id": location_id},
    )

    results["cycles"] = api.get(
        "/cycles",
        "Cycles",
        "known",
        {"page": 0, "size": 20},
    )

    results["orders"] = api.get(
        "/orders",
        "Orders",
        "known",
        {"page": 0, "size": 20},
    )

    results["order_items"] = api.get(
        "/order-items",
        "Order items",
        "known",
        {"page": 0, "size": 20},
    )

    results["reservations"] = api.get(
        "/reservations",
        "Active reservations",
        "known",
        {
            "page": 0,
            "size": 20,
            "status": "ACTIVE",
        },
    )

    results["wallet"] = api.get(
        "/account/wallet",
        "Wallet",
        "known",
    )

    results["wallet_mutations"] = api.get(
        "/account/wallet/mutations",
        "Wallet mutations",
        "known",
        {"page": 0, "size": 20},
    )

    results["notifications"] = api.get(
        "/notifications",
        "Notifications",
        "known",
        {"page": 0, "size": 20},
    )

    results["notifications_since_last_seen"] = api.get(
        "/notifications/since-last-seen",
        "Notifications / since-last-seen",
        "known",
    )

    results["notifications_chat"] = api.get(
        "/notifications/since-last-seen",
        "Notifications / CHAT",
        "known",
        {"category": "CHAT"},
    )

    results["notification_subscriptions"] = api.get(
        "/notifications/subscriptions",
        "Notification subscriptions",
        "known",
    )

    results["vouchers"] = api.get(
        "/vouchers",
        "Available vouchers",
        "known",
        {
            "page": 0,
            "size": 20,
            "status": "AVAILABLE",
        },
    )

    return results, location_id


# ---------------------------------------------------------------------------
# ID extraction
# ---------------------------------------------------------------------------

def collect_ids(results):
    machines = extract_items(
        results["machines"]["body"]
        if results.get("machines")
        else {}
    )

    cycles = extract_items(
        results["cycles"]["body"]
        if results.get("cycles")
        else {}
    )

    orders = extract_items(
        results["orders"]["body"]
        if results.get("orders")
        else {}
    )

    order_items = extract_items(
        results["order_items"]["body"]
        if results.get("order_items")
        else {}
    )

    reservations = extract_items(
        results["reservations"]["body"]
        if results.get("reservations")
        else {}
    )

    machine_ids = unique([
        extract_id(x) for x in machines
    ])

    cycle_ids = unique([
        extract_id(x) for x in cycles
    ])

    order_ids = unique([
        extract_id(x) for x in orders
    ])

    # Orders also appear inside cycles/order items.
    order_ids += [
        x.get("orderId")
        for x in cycles
        if isinstance(x, dict)
    ]

    order_ids += [
        x.get("orderId")
        for x in order_items
        if isinstance(x, dict)
    ]

    order_ids = unique(order_ids)

    order_item_ids = unique([
        extract_id(x) for x in order_items
    ])

    reservation_ids = unique([
        extract_id(x) for x in reservations
    ])

    fulfillment_ids = []

    for machine in machines:
        availability = (
            machine.get("availability") or {}
            if isinstance(machine, dict)
            else {}
        )

        fulfillment_ids.append(
            availability.get("fulfillmentId")
        )

    fulfillment_ids = unique(fulfillment_ids)

    return {
        "machine_ids": machine_ids,
        "cycle_ids": cycle_ids,
        "order_ids": order_ids,
        "order_item_ids": order_item_ids,
        "reservation_ids": reservation_ids,
        "fulfillment_ids": fulfillment_ids,
    }


# ---------------------------------------------------------------------------
# Detail endpoint tests
# ---------------------------------------------------------------------------

def test_detail_routes(api, ids):
    print("\n" + "=" * 78)
    print("DETAIL ENDPOINTS")
    print("=" * 78)

    for mid in ids["machine_ids"][:MAX_MACHINE_DETAILS]:
        encoded = quote(str(mid), safe="")

        api.get(
            f"/machines/{encoded}",
            f"Machine detail / {mid}",
            "detail",
        )

    for cid in ids["cycle_ids"][:MAX_CYCLE_DETAILS]:
        encoded = quote(str(cid), safe="")

        api.get(
            f"/cycles/{encoded}",
            f"Cycle detail / {cid}",
            "detail",
        )

    for oid in ids["order_ids"][:MAX_ORDER_DETAILS]:
        encoded = quote(str(oid), safe="")

        api.get(
            f"/orders/{encoded}",
            f"Order detail / {oid}",
            "detail",
        )

    for item_id in ids["order_item_ids"][:MAX_ORDER_ITEM_DETAILS]:
        encoded = quote(str(item_id), safe="")

        api.get(
            f"/order-items/{encoded}",
            f"Order-item detail / {item_id}",
            "detail",
        )

    for rid in ids["reservation_ids"][:MAX_RESERVATION_DETAILS]:
        encoded = quote(str(rid), safe="")

        api.get(
            f"/reservations/{encoded}",
            f"Reservation detail / {rid}",
            "detail",
        )


# ---------------------------------------------------------------------------
# Query parameter tests
# ---------------------------------------------------------------------------

def test_query_parameters(api, ids, location_id, known):
    print("\n" + "=" * 78)
    print("QUERY PARAMETER DISCOVERY")
    print("=" * 78)

    machine_id = (
        ids["machine_ids"][0]
        if ids["machine_ids"]
        else None
    )

    machine_code = None

    machines_body = (
        known["machines"]["body"]
        if known.get("machines")
        else {}
    )

    machines = extract_items(machines_body)

    if machines:
        machine_code = machines[0].get("code")

    cycle_id = (
        ids["cycle_ids"][0]
        if ids["cycle_ids"]
        else None
    )

    order_id = (
        ids["order_ids"][0]
        if ids["order_ids"]
        else None
    )

    # ------------------------------------------------------------
    # /locations
    #
    # We already know from the server response that machine.code
    # is a required parameter.
    # ------------------------------------------------------------

    if machine_code:
        api.get(
            "/locations",
            "Locations ?machine.code",
            "parameter",
            {"machine.code": machine_code},
        )

    # ------------------------------------------------------------
    # /machines
    # ------------------------------------------------------------

    machine_params = [
        ("location.id", location_id),
    ]

    if machine_id:
        machine_params.append(
            ("machine.id", machine_id)
        )

    if machine_code:
        machine_params.append(
            ("machine.code", machine_code)
        )

    for key, value in machine_params:
        api.get(
            "/machines",
            f"Machines ?{key}",
            "parameter",
            {key: value},
        )

    # ------------------------------------------------------------
    # /cycles
    # ------------------------------------------------------------

    cycle_params = [
        ("page", 0),
        ("size", 20),
    ]

    if machine_id:
        cycle_params.extend([
            ("machine.id", machine_id),
        ])

    if machine_code:
        cycle_params.extend([
            ("machine.code", machine_code),
        ])

    if location_id:
        cycle_params.extend([
            ("location.id", location_id),
        ])

    for key, value in cycle_params:
        api.get(
            "/cycles",
            f"Cycles ?{key}",
            "parameter",
            {key: value},
        )

    # ------------------------------------------------------------
    # /orders
    # ------------------------------------------------------------

    order_params = [
        ("page", 0),
        ("size", 20),
    ]

    if order_id:
        order_params.append(
            ("orderId", order_id)
        )

    if cycle_id:
        order_params.append(
            ("cycleId", cycle_id)
        )

    for key, value in order_params:
        api.get(
            "/orders",
            f"Orders ?{key}",
            "parameter",
            {key: value},
        )

    # ------------------------------------------------------------
    # /order-items
    # ------------------------------------------------------------

    order_item_params = [
        ("page", 0),
        ("size", 20),
        ("kind", "CYCLE"),
        ("kind", "RESERVATION"),
    ]

    for key, value in order_item_params:
        api.get(
            "/order-items",
            f"Order-items ?{key}={value}",
            "parameter",
            {key: value},
        )

    # ------------------------------------------------------------
    # /reservations
    # ------------------------------------------------------------

    reservation_params = [
        ("status", "ACTIVE"),
        ("status", "BOOKED"),
        ("page", 0),
        ("size", 20),
    ]

    for key, value in reservation_params:
        api.get(
            "/reservations",
            f"Reservations ?{key}={value}",
            "parameter",
            {key: value},
        )


# ---------------------------------------------------------------------------
# Relationship route tests
# ---------------------------------------------------------------------------

def test_relationships(api, ids):
    print("\n" + "=" * 78)
    print("RELATIONSHIP ROUTES")
    print("=" * 78)

    if ids["machine_ids"]:
        mid = quote(str(ids["machine_ids"][0]), safe="")

        candidates = [
            (
                f"/machines/{mid}/availability",
                "Machine -> availability",
            ),
            (
                f"/machines/{mid}/cycles",
                "Machine -> cycles",
            ),
            (
                f"/machines/{mid}/orders",
                "Machine -> orders",
            ),
            (
                f"/machines/{mid}/fulfillment",
                "Machine -> fulfillment",
            ),
        ]

        for path, label in candidates:
            api.get(
                path,
                f"Hypothesis: {label}",
                "relationship",
            )

    if ids["cycle_ids"]:
        cid = quote(str(ids["cycle_ids"][0]), safe="")

        candidates = [
            (
                f"/cycles/{cid}/machine",
                "Cycle -> machine",
            ),
            (
                f"/cycles/{cid}/order",
                "Cycle -> order",
            ),
            (
                f"/cycles/{cid}/fulfillment",
                "Cycle -> fulfillment",
            ),
            (
                f"/cycles/{cid}/status",
                "Cycle -> status",
            ),
        ]

        for path, label in candidates:
            api.get(
                path,
                f"Hypothesis: {label}",
                "relationship",
            )

    if ids["order_ids"]:
        oid = quote(str(ids["order_ids"][0]), safe="")

        candidates = [
            (
                f"/orders/{oid}/items",
                "Order -> items",
            ),
            (
                f"/orders/{oid}/payments",
                "Order -> payments",
            ),
            (
                f"/orders/{oid}/fulfillment",
                "Order -> fulfillment",
            ),
            (
                f"/orders/{oid}/cycles",
                "Order -> cycles",
            ),
        ]

        for path, label in candidates:
            api.get(
                path,
                f"Hypothesis: {label}",
                "relationship",
            )

    if ids["fulfillment_ids"]:
        fid = quote(
            str(ids["fulfillment_ids"][0]),
            safe="",
        )

        candidates = [
            (
                f"/fulfillments/{fid}",
                "Fulfillment detail",
            ),
            (
                f"/fulfillments/{fid}/status",
                "Fulfillment status",
            ),
            (
                f"/fulfillments/{fid}/cycle",
                "Fulfillment -> cycle",
            ),
            (
                f"/fulfillments/{fid}/machine",
                "Fulfillment -> machine",
            ),
        ]

        for path, label in candidates:
            api.get(
                path,
                f"Hypothesis: {label}",
                "relationship",
            )


# ---------------------------------------------------------------------------
# Documentation discovery
# ---------------------------------------------------------------------------

def test_documentation(api):
    print("\n" + "=" * 78)
    print("DOCUMENTATION DISCOVERY")
    print("=" * 78)

    candidates = [
        (
            f"{HOST}/v3/api-docs",
            "Root /v3/api-docs",
        ),
        (
            f"{HOST}/api-docs",
            "Root /api-docs",
        ),
        (
            f"{HOST}/swagger.json",
            "Root /swagger.json",
        ),
        (
            f"{HOST}/openapi.json",
            "Root /openapi.json",
        ),
        (
            f"{HOST}/swagger-ui.html",
            "Root /swagger-ui.html",
        ),
        (
            f"{HOST}/swagger-ui/index.html",
            "Root /swagger-ui/index.html",
        ),
        (
            f"{HOST}/appwash/v3/api-docs",
            "AppWash /v3/api-docs",
        ),
        (
            f"{HOST}/appwash/api-docs",
            "AppWash /api-docs",
        ),
        (
            f"{API_BASE}/v3/api-docs",
            "API /v3/api-docs",
        ),
        (
            f"{API_BASE}/swagger.json",
            "API /swagger.json",
        ),
        (
            f"{API_BASE}/openapi.json",
            "API /openapi.json",
        ),
    ]

    for url, label in candidates:
        api.get(
            url,
            label,
            "documentation",
        )


# ---------------------------------------------------------------------------
# State extraction
# ---------------------------------------------------------------------------

def extract_states(known):
    states = {}

    def add(resource, field, values):
        values = unique(values)

        if values:
            states.setdefault(resource, {})[field] = values

    machine_items = extract_items(
        known["machines"]["body"]
        if known.get("machines")
        else {}
    )

    cycle_items = extract_items(
        known["cycles"]["body"]
        if known.get("cycles")
        else {}
    )

    order_items = extract_items(
        known["orders"]["body"]
        if known.get("orders")
        else {}
    )

    order_line_items = extract_items(
        known["order_items"]["body"]
        if known.get("order_items")
        else {}
    )

    add(
        "machine",
        "availability.status",
        [
            (x.get("availability") or {}).get("status")
            for x in machine_items
        ],
    )

    add(
        "cycle",
        "status",
        [
            x.get("status")
            for x in cycle_items
        ],
    )

    add(
        "order",
        "status",
        [
            x.get("status")
            for x in order_items
        ],
    )

    add(
        "order",
        "paymentStatus",
        [
            x.get("paymentStatus")
            for x in order_items
        ],
    )

    add(
        "order",
        "fulfillmentStatus",
        [
            x.get("fulfillmentStatus")
            for x in order_items
        ],
    )

    add(
        "orderItem",
        "status",
        [
            x.get("status")
            for x in order_line_items
        ],
    )

    add(
        "orderItem",
        "fulfillmentStatus",
        [
            x.get("fulfillmentStatus")
            for x in order_line_items
        ],
    )

    return states


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def generate_report(output, api_results):
    lines = []

    lines.append("# AppWash API Finder v2 Report")
    lines.append("")
    lines.append(
        f"Generated: `{output['tested_at']}`"
    )
    lines.append("")
    lines.append("## Safety constraints")
    lines.append("")
    lines.append("- AppWash API requests: GET only")
    lines.append("- No mutation requests")
    lines.append("- No arbitrary UUID enumeration")
    lines.append("- No large endpoint wordlist")
    lines.append(
        f"- Request delay: {REQUEST_DELAY:.2f}s"
    )
    lines.append("")

    lines.append("## Authentication")
    lines.append("")
    lines.append(
        f"- Status: `{output['authentication']['status']}`"
    )
    lines.append("- Method: Cognito OAuth + PKCE")
    lines.append("")

    lines.append("## Confirmed / known endpoints")
    lines.append("")

    for result in api_results:
        if result.get("category") != "known":
            continue

        status = result.get("status")
        url = result.get("url")
        label = result.get("label")

        lines.append(
            f"- `{status}` `{label}` — `{url}`"
        )

    lines.append("")

    lines.append("## Newly interesting 2xx results")
    lines.append("")

    interesting = [
        x for x in api_results
        if x.get("category") != "known"
        and isinstance(x.get("status"), int)
        and 200 <= x["status"] < 300
    ]

    if not interesting:
        lines.append("No additional 2xx results.")
    else:
        for result in interesting:
            lines.append(
                f"- `{result['status']}` "
                f"`{result['label']}` — `{result['url']}`"
            )

    lines.append("")

    lines.append("## Parameter tests")
    lines.append("")

    parameter_results = [
        x for x in api_results
        if x.get("category") == "parameter"
    ]

    for result in parameter_results:
        lines.append(
            f"- `{result.get('status')}` "
            f"`{result.get('label')}`"
        )

    lines.append("")

    lines.append("## Relationship tests")
    lines.append("")

    relationship_results = [
        x for x in api_results
        if x.get("category") == "relationship"
    ]

    for result in relationship_results:
        lines.append(
            f"- `{result.get('status')}` "
            f"`{result.get('label')}`"
        )

    lines.append("")

    lines.append("## Resource IDs")
    lines.append("")

    for key, values in output["discovered_ids"].items():
        lines.append(
            f"- `{key}`: {len(values)}"
        )

    lines.append("")

    lines.append("## Observed states")
    lines.append("")

    states = output["states"]

    if not states:
        lines.append("No state fields extracted.")
    else:
        for resource, fields in states.items():
            lines.append(f"### {resource}")
            lines.append("")

            for field, values in fields.items():
                lines.append(
                    f"- `{field}`: "
                    + ", ".join(f"`{v}`" for v in values)
                )

            lines.append("")

    lines.append("## Documentation endpoints")
    lines.append("")

    docs = [
        x for x in api_results
        if x.get("category") == "documentation"
    ]

    for result in docs:
        lines.append(
            f"- `{result.get('status')}` "
            f"`{result.get('label')}` — "
            f"`{result.get('url')}`"
        )

    lines.append("")

    lines.append("## Errors / failed hypotheses")
    lines.append("")

    errors = [
        x for x in api_results
        if (
            isinstance(x.get("status"), int)
            and x.get("status") >= 400
        )
        or x.get("error")
    ]

    if not errors:
        lines.append("No errors.")
    else:
        for result in errors:
            status = result.get("status")
            label = result.get("label")
            url = result.get("url")

            lines.append(
                f"- `{status}` `{label}` — `{url}`"
            )

    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "A 2xx response indicates the tested route accepted the "
        "request. A 401 indicates authentication failure. A 403 "
        "can indicate that the resource exists but is not accessible "
        "to the current user. A 400 can be especially useful when "
        "the server explicitly identifies a required or invalid "
        "parameter. A 404 is not proof that an entire resource family "
        "does not exist."
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("APPWASH API FINDER V2")
    print("=" * 78)
    print("Read-only discovery. No mutation requests.")

    token = cognito_login()

    api = API(token)

    # Authentication sanity check.
    print("\n" + "=" * 78)
    print("AUTHENTICATION SANITY CHECK")
    print("=" * 78)

    auth_check = api.get(
        "/user",
        "Authentication check /user",
        "authentication",
    )

    if not auth_check:
        die("Authentication check failed")

    if auth_check.get("status") == 401:
        die(
            "Authentication failed with HTTP 401. "
            "No discovery requests will continue."
        )

    if auth_check.get("status") != 200:
        die(
            f"Authentication sanity check returned "
            f"HTTP {auth_check.get('status')}"
        )

    # Known endpoints.
    known, location_id = collect_known(api)

    # Extract IDs.
    ids = collect_ids(known)

    # Detail endpoints.
    test_detail_routes(api, ids)

    # Query parameters.
    test_query_parameters(
        api,
        ids,
        location_id,
        known,
    )

    # Relationship hypotheses.
    test_relationships(api, ids)

    # Swagger/OpenAPI locations.
    test_documentation(api)

    # States.
    states = extract_states(known)

    # Output.
    output = {
        "tested_at": datetime.now().astimezone().isoformat(),
        "api_base": API_BASE,
        "authentication": {
            "status": "OK",
            "method": "Cognito OAuth + PKCE",
        },
        "location_id": location_id,
        "discovered_ids": ids,
        "states": states,
        "results": api.results,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(
            output,
            fh,
            indent=2,
            ensure_ascii=False,
        )

    report = generate_report(
        output,
        api.results,
    )

    with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
        fh.write(report)

    # Summary.
    successful = [
        x for x in api.results
        if isinstance(x.get("status"), int)
        and 200 <= x["status"] < 300
    ]

    additional = [
        x for x in successful
        if x.get("category") != "known"
    ]

    print("\n" + "=" * 78)
    print("V2 DISCOVERY COMPLETE")
    print("=" * 78)
    print(f"Requests recorded:       {len(api.results)}")
    print(f"2xx responses:            {len(successful)}")
    print(f"Additional 2xx results:   {len(additional)}")
    print(f"JSON output:              {OUTPUT_JSON}")
    print(f"Markdown report:          {OUTPUT_MD}")

    print("\nADDITIONAL 2xx RESULTS:")

    if not additional:
        print("  None")
    else:
        for result in additional:
            print(
                f"  [{result['status']}] "
                f"{result['label']}"
            )
            print(
                f"      {result['url']}"
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)
    except requests.RequestException as exc:
        die(f"Network error: {exc}")
    except Exception as exc:
        die(f"Unexpected error: {exc}")
