"""Sample payloads captured from the current AppWash API."""
from __future__ import annotations

LOCATION_ID = "1f28f58a-63f5-43a1-a649-fc6cffd3daff"
OCCUPIED_MACHINE_ID = "a407d752-7478-4bb5-a018-3c149b47d1bc"
FREE_MACHINE_ID = "a49744f7-56c2-494d-b324-192ec87d0ca2"
FULFILLMENT_ID = "1125a4f3-a1c0-4aab-870a-de7c8c28dee4"
ORDER_ID = "b3b1a42a-673b-4c9a-88c9-8663e340d9cd"

OCCUPIED_MACHINE = {
    "id": OCCUPIED_MACHINE_ID,
    "code": "46084",
    "name": "46084",
    "productGroup": "WM",
    "location": {"id": LOCATION_ID},
    "availability": {
        "subjectType": "MACHINE",
        "subjectId": OCCUPIED_MACHINE_ID,
        "status": "OCCUPIED",
        "statusAtCheckedAt": "OCCUPIED",
        "statusSince": "2026-08-28T12:39:29.705243Z",
        "fulfillmentId": FULFILLMENT_ID,
        "checkedAt": "2026-08-28T13:24:14.723753417Z",
        "checkedFrom": "2026-08-28T13:24:14.7127584Z",
        "checkedUntil": "2026-08-28T15:24:14.7127584Z",
        "checkedFulfillmentId": None,
        "additionalInfo": (
            f"MACHINE {OCCUPIED_MACHINE_ID} is OCCUPIED from "
            "2026-08-28T12:39:29.705243Z to 2026-08-28T14:39:29.705243Z"
        ),
    },
    "additionalInfo": None,
    "cyclePricePreview": {"currency": "EUR", "total": 3.0, "type": "FIX_PRICE"},
}

FREE_MACHINE = {
    "id": FREE_MACHINE_ID,
    "code": "46115",
    "name": "46115",
    "productGroup": "TD",
    "location": {"id": LOCATION_ID},
    "availability": {
        "subjectType": "MACHINE",
        "subjectId": FREE_MACHINE_ID,
        "status": "FREE",
        "statusAtCheckedAt": "FREE",
        "statusSince": None,
        "fulfillmentId": None,
        "checkedAt": "2026-08-28T13:24:14.732343008Z",
        "checkedFrom": "2026-08-28T13:24:14.724095021Z",
        "checkedUntil": "2026-08-28T15:24:14.724095021Z",
        "checkedFulfillmentId": None,
        "additionalInfo": (
            f"MACHINE {FREE_MACHINE_ID} is FREE from "
            "2026-08-28T13:24:14.724095021Z to 2026-08-28T15:24:14.724095021Z"
        ),
    },
    "additionalInfo": None,
    "cyclePricePreview": {"currency": "EUR", "total": 2.0, "type": "FIX_PRICE"},
}

MACHINES_RESPONSE = {"items": [OCCUPIED_MACHINE, FREE_MACHINE]}

ACTIVE_CYCLE = {
    "id": FULFILLMENT_ID,
    "machine": {
        "id": OCCUPIED_MACHINE_ID,
        "name": "46084",
        "code": "46084",
        "productGroup": "WM",
    },
    "location": {
        "id": LOCATION_ID,
        "name": "Hamburg - Borgfelder Strasse 16 | Borgfelder Strasse 16",
    },
    "productConfiguration": {"type": "FIX_CYCLE_WASHING", "kind": "CYCLE"},
    "orderId": ORDER_ID,
    "status": "ENABLED",
    "terminationReason": None,
    "createdAt": "2026-08-28T12:39:12.490686Z",
    "orderedAt": "2026-08-28T12:39:18.626745Z",
    "enabledAt": "2026-08-28T12:39:29.705243Z",
    "stoppedAt": None,
}

STOPPED_CYCLE = {
    **ACTIVE_CYCLE,
    "id": "0f0f0f0f-0000-4000-8000-000000000001",
    "status": "STOPPED",
    "terminationReason": "COMPLETED",
    "stoppedAt": "2026-08-28T13:39:29.705243Z",
}

CYCLES_RESPONSE = {
    "items": [ACTIVE_CYCLE, STOPPED_CYCLE],
    "total": 2,
    "pageNumber": 0,
    "pageSize": 20,
}

ORDERS_RESPONSE = {
    "items": [
        {
            "id": ORDER_ID,
            "status": "BOOKED",
            "billingMode": "PREPAID",
            "paymentStatus": "SETTLED",
            "currency": "EUR",
            "fulfillmentStatus": "FULFILLING",
            "productItems": [
                {
                    "instance": {
                        "type": "FIX_CYCLE_WASHING",
                        "id": FULFILLMENT_ID,
                        "name": "Washing",
                        "description": "Machine: 46084",
                        "kind": "CYCLE",
                    }
                }
            ],
        }
    ],
    "total": 1,
    "pageNumber": 0,
    "pageSize": 20,
}

WALLET_RESPONSE = {
    "currency": "EUR",
    "balance": 3.0,
    "availableBalance": 3.0,
    "totalBalance": 3.0,
    "authorizedBalance": 0.0,
}

USER_RESPONSE = {
    "id": "d0cc693c-20a1-70d6-e03d-d2f515c50c77",
    "email": "user@example.com",
    "preferredLocation": {
        "id": LOCATION_ID,
        "name": "Hamburg - Borgfelder Strasse 16 | Borgfelder Strasse 16",
    },
    "type": "USER",
}
