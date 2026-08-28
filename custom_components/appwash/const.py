"""Constants for the AppWash integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "appwash"
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_LOCATION_ID: Final = "location_id"
CONF_LOCATION_NAME: Final = "location_name"

DEFAULT_SCAN_INTERVAL: Final = 60

# Current AppWash / Miele MOVE application API.
API_BASE_URL: Final = "https://www.miele-move.com/appwash/api/app/v1"

# Amazon Cognito hosted UI used by the current AppWash web application.
COGNITO_URL: Final = "https://appwash.auth.eu-north-1.amazoncognito.com"
COGNITO_CLIENT_ID: Final = "24n99a16tg55iaclg2frjrma32"
COGNITO_REDIRECT_URI: Final = "https://web.appwash.com/auth-callback"
COGNITO_SCOPE: Final = "openid email phone profile aws.cognito.signin.user.admin"

# Sent by the web frontend on every API call.
APP_HEADER: Final = "web/3.4.0"
WEB_ORIGIN: Final = "https://web.appwash.com"

REQUEST_TIMEOUT: Final = 30

# Product groups returned by ``machine.productGroup``.
PRODUCT_GROUP_WASHER: Final = "WM"
PRODUCT_GROUP_DRYER: Final = "TD"

# Availability states observed on ``machine.availability.status``.
STATE_FREE: Final = "FREE"
STATE_OCCUPIED: Final = "OCCUPIED"
STATE_UNKNOWN: Final = "UNKNOWN"

# Cycle states observed on ``cycle.status``.
CYCLE_STATE_ENABLED: Final = "ENABLED"

ATTR_AVAILABLE: Final = "available"
ATTR_OCCUPIED: Final = "occupied"
ATTR_STATUS: Final = "status"

ATTR_MACHINE_CODE: Final = "machine_code"
ATTR_MACHINE_NAME: Final = "machine_name"
ATTR_MACHINE_ID: Final = "machine_id"
ATTR_PRODUCT_GROUP: Final = "product_group"
ATTR_AVAILABILITY_STATUS: Final = "availability_status"
ATTR_STATUS_SINCE: Final = "status_since"
ATTR_FULFILLMENT_ID: Final = "fulfillment_id"
ATTR_CHECKED_AT: Final = "checked_at"
ATTR_CHECKED_FROM: Final = "checked_from"
ATTR_CHECKED_UNTIL: Final = "checked_until"
ATTR_CYCLE_PRICE: Final = "cycle_price"
ATTR_CURRENCY: Final = "currency"
ATTR_ADDITIONAL_INFO: Final = "additional_info"
ATTR_LOCATION_ID: Final = "location_id"
ATTR_ESTIMATED_END: Final = "estimated_end"
ATTR_REMAINING_MINUTES: Final = "remaining_minutes"
