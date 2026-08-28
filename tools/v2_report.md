# AppWash API Finder v2 Report

Generated: `2026-08-28T15:25:44.342635+02:00`

## Safety constraints

- AppWash API requests: GET only
- No mutation requests
- No arbitrary UUID enumeration
- No large endpoint wordlist
- Request delay: 0.40s

## Authentication

- Status: `OK`
- Method: Cognito OAuth + PKCE

## Confirmed / known endpoints

- `200` `Config / well-known` — `https://www.miele-move.com/appwash/api/app/v1/config/well-known`
- `200` `Config / countries` — `https://www.miele-move.com/appwash/api/app/v1/config/countries`
- `200` `Config / topups` — `https://www.miele-move.com/appwash/api/app/v1/config/topups?currency=EUR`
- `200` `Current user` — `https://www.miele-move.com/appwash/api/app/v1/user`
- `200` `Location detail` — `https://www.miele-move.com/appwash/api/app/v1/locations/1f28f58a-63f5-43a1-a649-fc6cffd3daff`
- `200` `Machines by location` — `https://www.miele-move.com/appwash/api/app/v1/machines?location.id=1f28f58a-63f5-43a1-a649-fc6cffd3daff`
- `200` `Cycles` — `https://www.miele-move.com/appwash/api/app/v1/cycles?page=0&size=20`
- `200` `Orders` — `https://www.miele-move.com/appwash/api/app/v1/orders?page=0&size=20`
- `200` `Order items` — `https://www.miele-move.com/appwash/api/app/v1/order-items?page=0&size=20`
- `200` `Active reservations` — `https://www.miele-move.com/appwash/api/app/v1/reservations?page=0&size=20&status=ACTIVE`
- `200` `Wallet` — `https://www.miele-move.com/appwash/api/app/v1/account/wallet`
- `200` `Wallet mutations` — `https://www.miele-move.com/appwash/api/app/v1/account/wallet/mutations?page=0&size=20`
- `200` `Notifications` — `https://www.miele-move.com/appwash/api/app/v1/notifications?page=0&size=20`
- `200` `Notifications / since-last-seen` — `https://www.miele-move.com/appwash/api/app/v1/notifications/since-last-seen`
- `200` `Notifications / CHAT` — `https://www.miele-move.com/appwash/api/app/v1/notifications/since-last-seen?category=CHAT`
- `200` `Notification subscriptions` — `https://www.miele-move.com/appwash/api/app/v1/notifications/subscriptions`
- `200` `Available vouchers` — `https://www.miele-move.com/appwash/api/app/v1/vouchers?page=0&size=20&status=AVAILABLE`

## Newly interesting 2xx results

- `200` `Authentication check /user` — `https://www.miele-move.com/appwash/api/app/v1/user`
- `200` `Machine detail / 138fdb8c-1a07-40f6-b11e-31350015ef14` — `https://www.miele-move.com/appwash/api/app/v1/machines/138fdb8c-1a07-40f6-b11e-31350015ef14`
- `200` `Machine detail / a49744f7-56c2-494d-b324-192ec87d0ca2` — `https://www.miele-move.com/appwash/api/app/v1/machines/a49744f7-56c2-494d-b324-192ec87d0ca2`
- `200` `Machine detail / 87e17511-1752-48a6-9e34-829c35c139cf` — `https://www.miele-move.com/appwash/api/app/v1/machines/87e17511-1752-48a6-9e34-829c35c139cf`
- `200` `Cycle detail / 1125a4f3-a1c0-4aab-870a-de7c8c28dee4` — `https://www.miele-move.com/appwash/api/app/v1/cycles/1125a4f3-a1c0-4aab-870a-de7c8c28dee4`
- `200` `Order detail / 9c4e590a-4851-477c-84ca-2641b68e1ec0` — `https://www.miele-move.com/appwash/api/app/v1/orders/9c4e590a-4851-477c-84ca-2641b68e1ec0`
- `200` `Order detail / adcb7a36-b968-4dc3-95a3-b624f8c9656b` — `https://www.miele-move.com/appwash/api/app/v1/orders/adcb7a36-b968-4dc3-95a3-b624f8c9656b`
- `200` `Order detail / 670ace3a-2a2e-4e64-9b5e-05e29058035a` — `https://www.miele-move.com/appwash/api/app/v1/orders/670ace3a-2a2e-4e64-9b5e-05e29058035a`
- `200` `Order-item detail / c8d9dede-3d17-453e-aa2a-fdb61d442b41$0` — `https://www.miele-move.com/appwash/api/app/v1/order-items/c8d9dede-3d17-453e-aa2a-fdb61d442b41%240`
- `200` `Order-item detail / b3b1a42a-673b-4c9a-88c9-8663e340d9cd$0` — `https://www.miele-move.com/appwash/api/app/v1/order-items/b3b1a42a-673b-4c9a-88c9-8663e340d9cd%240`
- `200` `Locations ?machine.code` — `https://www.miele-move.com/appwash/api/app/v1/locations?machine.code=46113`
- `200` `Machines ?location.id` — `https://www.miele-move.com/appwash/api/app/v1/machines?location.id=1f28f58a-63f5-43a1-a649-fc6cffd3daff`
- `200` `Cycles ?page` — `https://www.miele-move.com/appwash/api/app/v1/cycles?page=0`
- `200` `Cycles ?size` — `https://www.miele-move.com/appwash/api/app/v1/cycles?size=20`
- `200` `Cycles ?machine.id` — `https://www.miele-move.com/appwash/api/app/v1/cycles?machine.id=138fdb8c-1a07-40f6-b11e-31350015ef14`
- `200` `Cycles ?machine.code` — `https://www.miele-move.com/appwash/api/app/v1/cycles?machine.code=46113`
- `200` `Cycles ?location.id` — `https://www.miele-move.com/appwash/api/app/v1/cycles?location.id=1f28f58a-63f5-43a1-a649-fc6cffd3daff`
- `200` `Orders ?page` — `https://www.miele-move.com/appwash/api/app/v1/orders?page=0`
- `200` `Orders ?size` — `https://www.miele-move.com/appwash/api/app/v1/orders?size=20`
- `200` `Orders ?orderId` — `https://www.miele-move.com/appwash/api/app/v1/orders?orderId=9c4e590a-4851-477c-84ca-2641b68e1ec0`
- `200` `Orders ?cycleId` — `https://www.miele-move.com/appwash/api/app/v1/orders?cycleId=1125a4f3-a1c0-4aab-870a-de7c8c28dee4`
- `200` `Order-items ?page=0` — `https://www.miele-move.com/appwash/api/app/v1/order-items?page=0`
- `200` `Order-items ?size=20` — `https://www.miele-move.com/appwash/api/app/v1/order-items?size=20`
- `200` `Order-items ?kind=CYCLE` — `https://www.miele-move.com/appwash/api/app/v1/order-items?kind=CYCLE`
- `200` `Order-items ?kind=RESERVATION` — `https://www.miele-move.com/appwash/api/app/v1/order-items?kind=RESERVATION`
- `200` `Reservations ?status=ACTIVE` — `https://www.miele-move.com/appwash/api/app/v1/reservations?status=ACTIVE`
- `200` `Reservations ?page=0` — `https://www.miele-move.com/appwash/api/app/v1/reservations?page=0`
- `200` `Reservations ?size=20` — `https://www.miele-move.com/appwash/api/app/v1/reservations?size=20`
- `200` `Root /swagger.json` — `https://www.miele-move.com/swagger.json`
- `200` `Root /openapi.json` — `https://www.miele-move.com/openapi.json`
- `200` `Root /swagger-ui.html` — `https://www.miele-move.com/swagger-ui.html`
- `200` `Root /swagger-ui/index.html` — `https://www.miele-move.com/swagger-ui/index.html`

## Parameter tests

- `200` `Locations ?machine.code`
- `200` `Machines ?location.id`
- `None` `Machines ?machine.id`
- `None` `Machines ?machine.code`
- `200` `Cycles ?page`
- `200` `Cycles ?size`
- `200` `Cycles ?machine.id`
- `200` `Cycles ?machine.code`
- `200` `Cycles ?location.id`
- `200` `Orders ?page`
- `200` `Orders ?size`
- `200` `Orders ?orderId`
- `200` `Orders ?cycleId`
- `200` `Order-items ?page=0`
- `200` `Order-items ?size=20`
- `200` `Order-items ?kind=CYCLE`
- `200` `Order-items ?kind=RESERVATION`
- `200` `Reservations ?status=ACTIVE`
- `400` `Reservations ?status=BOOKED`
- `200` `Reservations ?page=0`
- `200` `Reservations ?size=20`

## Relationship tests

- `404` `Hypothesis: Machine -> availability`
- `404` `Hypothesis: Machine -> cycles`
- `404` `Hypothesis: Machine -> orders`
- `404` `Hypothesis: Machine -> fulfillment`
- `404` `Hypothesis: Cycle -> machine`
- `404` `Hypothesis: Cycle -> order`
- `404` `Hypothesis: Cycle -> fulfillment`
- `404` `Hypothesis: Cycle -> status`
- `404` `Hypothesis: Order -> items`
- `404` `Hypothesis: Order -> payments`
- `404` `Hypothesis: Order -> fulfillment`
- `404` `Hypothesis: Order -> cycles`
- `404` `Hypothesis: Fulfillment detail`
- `404` `Hypothesis: Fulfillment status`
- `404` `Hypothesis: Fulfillment -> cycle`
- `404` `Hypothesis: Fulfillment -> machine`

## Resource IDs

- `machine_ids`: 12
- `cycle_ids`: 1
- `order_ids`: 8
- `order_item_ids`: 2
- `reservation_ids`: 0
- `fulfillment_ids`: 2

## Observed states

### machine

- `availability.status`: `OCCUPIED`, `FREE`

### cycle

- `status`: `ENABLED`

### order

- `status`: `DRAFT`, `BOOKED`
- `paymentStatus`: `UNSETTLED`, `SETTLED`

### orderItem

- `status`: `BOOKED`
- `fulfillmentStatus`: `FULFILLED`, `FULFILLING`

## Documentation endpoints

- `401` `Root /v3/api-docs` — `https://www.miele-move.com/v3/api-docs`
- `401` `Root /api-docs` — `https://www.miele-move.com/api-docs`
- `200` `Root /swagger.json` — `https://www.miele-move.com/swagger.json`
- `200` `Root /openapi.json` — `https://www.miele-move.com/openapi.json`
- `200` `Root /swagger-ui.html` — `https://www.miele-move.com/swagger-ui.html`
- `200` `Root /swagger-ui/index.html` — `https://www.miele-move.com/swagger-ui/index.html`
- `401` `AppWash /v3/api-docs` — `https://www.miele-move.com/appwash/v3/api-docs`
- `401` `AppWash /api-docs` — `https://www.miele-move.com/appwash/api-docs`
- `401` `API /v3/api-docs` — `https://www.miele-move.com/appwash/api/app/v1/v3/api-docs`
- `404` `API /swagger.json` — `https://www.miele-move.com/appwash/api/app/v1/swagger.json`
- `404` `API /openapi.json` — `https://www.miele-move.com/appwash/api/app/v1/openapi.json`

## Errors / failed hypotheses

- `None` `Machines ?machine.id` — `https://www.miele-move.com/appwash/api/app/v1/machines`
- `None` `Machines ?machine.code` — `https://www.miele-move.com/appwash/api/app/v1/machines`
- `400` `Reservations ?status=BOOKED` — `https://www.miele-move.com/appwash/api/app/v1/reservations?status=BOOKED`
- `404` `Hypothesis: Machine -> availability` — `https://www.miele-move.com/appwash/api/app/v1/machines/138fdb8c-1a07-40f6-b11e-31350015ef14/availability`
- `404` `Hypothesis: Machine -> cycles` — `https://www.miele-move.com/appwash/api/app/v1/machines/138fdb8c-1a07-40f6-b11e-31350015ef14/cycles`
- `404` `Hypothesis: Machine -> orders` — `https://www.miele-move.com/appwash/api/app/v1/machines/138fdb8c-1a07-40f6-b11e-31350015ef14/orders`
- `404` `Hypothesis: Machine -> fulfillment` — `https://www.miele-move.com/appwash/api/app/v1/machines/138fdb8c-1a07-40f6-b11e-31350015ef14/fulfillment`
- `404` `Hypothesis: Cycle -> machine` — `https://www.miele-move.com/appwash/api/app/v1/cycles/1125a4f3-a1c0-4aab-870a-de7c8c28dee4/machine`
- `404` `Hypothesis: Cycle -> order` — `https://www.miele-move.com/appwash/api/app/v1/cycles/1125a4f3-a1c0-4aab-870a-de7c8c28dee4/order`
- `404` `Hypothesis: Cycle -> fulfillment` — `https://www.miele-move.com/appwash/api/app/v1/cycles/1125a4f3-a1c0-4aab-870a-de7c8c28dee4/fulfillment`
- `404` `Hypothesis: Cycle -> status` — `https://www.miele-move.com/appwash/api/app/v1/cycles/1125a4f3-a1c0-4aab-870a-de7c8c28dee4/status`
- `404` `Hypothesis: Order -> items` — `https://www.miele-move.com/appwash/api/app/v1/orders/9c4e590a-4851-477c-84ca-2641b68e1ec0/items`
- `404` `Hypothesis: Order -> payments` — `https://www.miele-move.com/appwash/api/app/v1/orders/9c4e590a-4851-477c-84ca-2641b68e1ec0/payments`
- `404` `Hypothesis: Order -> fulfillment` — `https://www.miele-move.com/appwash/api/app/v1/orders/9c4e590a-4851-477c-84ca-2641b68e1ec0/fulfillment`
- `404` `Hypothesis: Order -> cycles` — `https://www.miele-move.com/appwash/api/app/v1/orders/9c4e590a-4851-477c-84ca-2641b68e1ec0/cycles`
- `404` `Hypothesis: Fulfillment detail` — `https://www.miele-move.com/appwash/api/app/v1/fulfillments/eb9d8ca0-8abe-4b94-a02a-3d8929d2397b`
- `404` `Hypothesis: Fulfillment status` — `https://www.miele-move.com/appwash/api/app/v1/fulfillments/eb9d8ca0-8abe-4b94-a02a-3d8929d2397b/status`
- `404` `Hypothesis: Fulfillment -> cycle` — `https://www.miele-move.com/appwash/api/app/v1/fulfillments/eb9d8ca0-8abe-4b94-a02a-3d8929d2397b/cycle`
- `404` `Hypothesis: Fulfillment -> machine` — `https://www.miele-move.com/appwash/api/app/v1/fulfillments/eb9d8ca0-8abe-4b94-a02a-3d8929d2397b/machine`
- `401` `Root /v3/api-docs` — `https://www.miele-move.com/v3/api-docs`
- `401` `Root /api-docs` — `https://www.miele-move.com/api-docs`
- `401` `AppWash /v3/api-docs` — `https://www.miele-move.com/appwash/v3/api-docs`
- `401` `AppWash /api-docs` — `https://www.miele-move.com/appwash/api-docs`
- `401` `API /v3/api-docs` — `https://www.miele-move.com/appwash/api/app/v1/v3/api-docs`
- `404` `API /swagger.json` — `https://www.miele-move.com/appwash/api/app/v1/swagger.json`
- `404` `API /openapi.json` — `https://www.miele-move.com/appwash/api/app/v1/openapi.json`

## Interpretation

A 2xx response indicates the tested route accepted the request. A 401 indicates authentication failure. A 403 can indicate that the resource exists but is not accessible to the current user. A 400 can be especially useful when the server explicitly identifies a required or invalid parameter. A 404 is not proof that an entire resource family does not exist.