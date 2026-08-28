"""Normalized data models for the current AppWash API.

The AppWash/Miele MOVE API returns nested JSON documents.  Everything that
knows about the wire format lives here so that the coordinator and the
entities only ever deal with the small, flat objects below.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from .const import (
    CYCLE_STATE_ENABLED,
    OWNER_OTHER,
    OWNER_YOU,
    STATE_YOUR_CYCLE,
    PRODUCT_GROUP_DRYER,
    PRODUCT_GROUP_WASHER,
    STATE_FREE,
    STATE_OCCUPIED,
    STATE_UNKNOWN,
)

# ``MACHINE <uuid> is OCCUPIED from <iso> to <iso>``
_ADDITIONAL_INFO_RE = re.compile(
    r"\bfrom\s+(?P<start>\S+)\s+to\s+(?P<end>\S+)",
)

# The API emits up to nanosecond precision, which ``fromisoformat`` rejects.
_FRACTION_RE = re.compile(r"(\.\d{1,6})\d*")


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an API timestamp into an aware datetime, or None."""
    if not isinstance(value, str) or not value:
        return None

    text = _FRACTION_RE.sub(r"\1", value.strip())

    if text.endswith(("Z", "z")):
        text = f"{text[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def _as_dict(value: Any) -> dict[str, Any]:
    """Return a mapping for a possibly missing/null nested object."""
    return value if isinstance(value, dict) else {}


def _items(payload: Any) -> list[dict[str, Any]]:
    """Return the item list of a collection response.

    Current collection endpoints answer with ``{"items": [...], "total": n}``.
    A bare list is accepted as well so the parser stays forgiving.
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [x for x in payload["items"] if isinstance(x, dict)]

    return []


@dataclass(frozen=True)
class Cycle:
    """A washing/drying cycle as returned by ``GET /cycles``."""

    cycle_id: str
    machine_id: str | None = None
    machine_code: str | None = None
    machine_name: str | None = None
    location_id: str | None = None
    product_type: str | None = None
    product_kind: str | None = None
    order_id: str | None = None
    status: str | None = None
    termination_reason: str | None = None
    created_at: str | None = None
    ordered_at: str | None = None
    enabled_at: str | None = None
    stopped_at: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Cycle":
        """Build a cycle from a ``/cycles`` item."""
        machine = _as_dict(data.get("machine"))
        location = _as_dict(data.get("location"))
        product = _as_dict(data.get("productConfiguration"))

        return cls(
            cycle_id=data.get("id"),
            machine_id=machine.get("id"),
            machine_code=machine.get("code"),
            machine_name=machine.get("name"),
            location_id=location.get("id"),
            product_type=product.get("type"),
            product_kind=product.get("kind"),
            order_id=data.get("orderId"),
            status=data.get("status"),
            termination_reason=data.get("terminationReason"),
            created_at=data.get("createdAt"),
            ordered_at=data.get("orderedAt"),
            enabled_at=data.get("enabledAt"),
            stopped_at=data.get("stoppedAt"),
        )

    @property
    def is_active(self) -> bool:
        """Return True while the cycle is running."""
        return self.status == CYCLE_STATE_ENABLED and not self.stopped_at

    def as_attributes(self) -> dict[str, Any]:
        """Return the cycle as Home Assistant state attributes."""
        return {
            "cycle_id": self.cycle_id,
            "cycle_status": self.status,
            "cycle_product_type": self.product_type,
            "cycle_product_kind": self.product_kind,
            "cycle_order_id": self.order_id,
            "cycle_termination_reason": self.termination_reason,
            "cycle_created_at": self.created_at,
            "cycle_ordered_at": self.ordered_at,
            "cycle_enabled_at": self.enabled_at,
            "cycle_stopped_at": self.stopped_at,
        }


@dataclass(frozen=True)
class OrderItem:
    """A billed order line as returned by ``GET /order-items``.

    ``productId`` is the cycle id, which is how a line is tied back to the
    machine running it.
    """

    item_id: str
    order_id: str | None = None
    ordered_at: str | None = None
    status: str | None = None
    fulfillment_status: str | None = None
    product_type: str | None = None
    product_kind: str | None = None
    product_id: str | None = None
    product_name: str | None = None
    product_description: str | None = None
    gross_total_amount: float | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "OrderItem":
        """Build an order item from an ``/order-items`` item."""
        return cls(
            item_id=data.get("id"),
            order_id=data.get("orderId"),
            ordered_at=data.get("orderedAt"),
            status=data.get("status"),
            fulfillment_status=data.get("fulfillmentStatus"),
            product_type=data.get("productType"),
            product_kind=data.get("productKind"),
            product_id=data.get("productId"),
            product_name=data.get("productName"),
            product_description=data.get("productDescription"),
            gross_total_amount=data.get("grossTotalAmount"),
        )

    def as_attributes(self) -> dict[str, Any]:
        """Return the order line as Home Assistant state attributes."""
        return {
            "cycle_order_status": self.status,
            "cycle_fulfillment_status": self.fulfillment_status,
            "cycle_paid_amount": self.gross_total_amount,
            "cycle_description": self.product_description,
        }


@dataclass(frozen=True)
class Machine:
    """A machine as returned by ``GET /machines?location.id=...``."""

    machine_id: str
    code: str | None = None
    name: str | None = None
    product_group: str | None = None
    location_id: str | None = None
    availability_status: str = STATE_UNKNOWN
    status_at_checked_at: str | None = None
    status_since: str | None = None
    fulfillment_id: str | None = None
    checked_at: str | None = None
    checked_from: str | None = None
    checked_until: str | None = None
    additional_info: str | None = None
    cycle_price: float | None = None
    currency: str | None = None
    price_type: str | None = None
    cycle: Cycle | None = field(default=None, compare=False)
    order_item: OrderItem | None = field(default=None, compare=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Machine":
        """Build a machine from a ``/machines`` item."""
        availability = _as_dict(data.get("availability"))
        price = _as_dict(data.get("cyclePricePreview"))
        location = _as_dict(data.get("location"))

        code = data.get("code")
        status = availability.get("status") or STATE_UNKNOWN

        return cls(
            machine_id=data.get("id"),
            code=code,
            name=data.get("name") or code,
            product_group=data.get("productGroup"),
            location_id=location.get("id"),
            availability_status=status,
            status_at_checked_at=availability.get("statusAtCheckedAt"),
            status_since=availability.get("statusSince"),
            fulfillment_id=availability.get("fulfillmentId"),
            checked_at=availability.get("checkedAt"),
            checked_from=availability.get("checkedFrom"),
            checked_until=availability.get("checkedUntil"),
            # ``availability.additionalInfo`` carries the human readable
            # occupancy window; the machine level field is usually null.
            additional_info=(
                availability.get("additionalInfo")
                or data.get("additionalInfo")
            ),
            cycle_price=price.get("total"),
            currency=price.get("currency"),
            price_type=price.get("type"),
        )

    def with_cycle(self, cycle: Cycle | None) -> "Machine":
        """Return a copy of this machine with an associated cycle."""
        if cycle is None:
            return self

        return replace(self, cycle=cycle)

    def with_order_item(self, order_item: OrderItem | None) -> "Machine":
        """Return a copy of this machine with the cycle's billing line."""
        if order_item is None:
            return self

        return replace(self, order_item=order_item)

    @property
    def is_free(self) -> bool:
        """Return True when the machine can be used."""
        return self.availability_status == STATE_FREE

    @property
    def is_occupied(self) -> bool:
        """Return True when the machine is running/blocked."""
        return self.availability_status == STATE_OCCUPIED

    @property
    def is_own_cycle(self) -> bool:
        """Return True when a cycle of this account runs on the machine.

        ``GET /cycles`` only ever returns the authenticated account's own
        cycles, so an attached cycle is by definition yours.
        """
        return self.cycle is not None

    @property
    def occupied_by(self) -> str | None:
        """Return who the machine is occupied by, or None when it is free."""
        if not self.is_occupied:
            return None

        return OWNER_YOU if self.is_own_cycle else OWNER_OTHER

    @property
    def state(self) -> str:
        """Return the state reported to Home Assistant.

        ``OCCUPIED`` is narrowed to ``YOUR_CYCLE`` when the occupancy
        belongs to this account.  Every other availability value is passed
        through exactly as the API reported it.
        """
        if self.is_occupied and self.is_own_cycle:
            return STATE_YOUR_CYCLE

        return self.availability_status

    @property
    def is_washing_machine(self) -> bool:
        """Return True for washers."""
        return self.product_group == PRODUCT_GROUP_WASHER

    @property
    def is_dryer(self) -> bool:
        """Return True for tumble dryers."""
        return self.product_group == PRODUCT_GROUP_DRYER

    @property
    def estimated_end(self) -> datetime | None:
        """Return when the current occupancy is expected to end.

        The API does not expose a remaining-time field.  ``additionalInfo``
        does contain the occupancy window the backend calculated, e.g.
        ``MACHINE <id> is OCCUPIED from <start> to <end>``.
        """
        if not self.is_occupied or not self.additional_info:
            return None

        match = _ADDITIONAL_INFO_RE.search(self.additional_info)

        if match is None:
            return None

        return parse_timestamp(match.group("end"))

    @property
    def occupied_since(self) -> datetime | None:
        """Return when the current occupancy started."""
        return parse_timestamp(self.status_since)

    @property
    def cycle_duration_minutes(self) -> int | None:
        """Return the length of the occupancy window in minutes."""
        start = self.occupied_since
        end = self.estimated_end

        if start is None or end is None:
            return None

        return max(0, int(round((end - start).total_seconds() / 60)))

    def elapsed_minutes(self, now: datetime | None = None) -> int | None:
        """Return how long the current occupancy has been running."""
        start = self.occupied_since

        if start is None or not self.is_occupied:
            return None

        reference = now or datetime.now(timezone.utc)

        return max(0, int(round((reference - start).total_seconds() / 60)))

    def progress_percent(self, now: datetime | None = None) -> int | None:
        """Return how far through the occupancy window the machine is."""
        duration = self.cycle_duration_minutes
        elapsed = self.elapsed_minutes(now)

        if not duration or elapsed is None:
            return None

        return max(0, min(100, int(round(elapsed / duration * 100))))

    def remaining_minutes(self, now: datetime | None = None) -> int | None:
        """Return the minutes left of the current occupancy window."""
        end = self.estimated_end

        if end is None:
            return None

        reference = now or datetime.now(timezone.utc)
        remaining = (end - reference).total_seconds() / 60

        return max(0, int(round(remaining)))

    def as_attributes(self, now: datetime | None = None) -> dict[str, Any]:
        """Return the machine as Home Assistant state attributes."""
        end = self.estimated_end

        attributes: dict[str, Any] = {
            "machine_code": self.code,
            "machine_name": self.name,
            "machine_id": self.machine_id,
            "product_group": self.product_group,
            "location_id": self.location_id,
            "availability_status": self.availability_status,
            "is_own_cycle": self.is_own_cycle,
            "occupied_by": self.occupied_by,
            "status_since": self.status_since,
            "fulfillment_id": self.fulfillment_id,
            "checked_at": self.checked_at,
            "checked_from": self.checked_from,
            "checked_until": self.checked_until,
            "cycle_price": self.cycle_price,
            "currency": self.currency,
            "price_type": self.price_type,
            "additional_info": self.additional_info,
            "estimated_end": end.isoformat() if end else None,
            "remaining_minutes": self.remaining_minutes(now),
            "elapsed_minutes": self.elapsed_minutes(now),
            "cycle_duration_minutes": self.cycle_duration_minutes,
            "progress_percent": self.progress_percent(now),
        }

        if self.cycle is not None:
            attributes.update(self.cycle.as_attributes())

        if self.order_item is not None:
            attributes.update(self.order_item.as_attributes())

        return attributes


def parse_machines(payload: Any) -> list[Machine]:
    """Parse a ``GET /machines`` response."""
    return [
        Machine.from_api(item)
        for item in _items(payload)
        if item.get("id")
    ]


def parse_cycles(payload: Any) -> list[Cycle]:
    """Parse a ``GET /cycles`` response."""
    return [
        Cycle.from_api(item)
        for item in _items(payload)
        if item.get("id")
    ]


def active_cycles_by_machine(cycles: list[Cycle]) -> dict[str, Cycle]:
    """Map machine id -> active cycle.

    ``GET /cycles`` returns the newest cycles first, so the first active
    cycle seen for a machine wins.
    """
    mapping: dict[str, Cycle] = {}

    for cycle in cycles:
        if not cycle.is_active or not cycle.machine_id:
            continue

        mapping.setdefault(cycle.machine_id, cycle)

    return mapping


def parse_order_items(payload: Any) -> list[OrderItem]:
    """Parse a ``GET /order-items`` response."""
    return [
        OrderItem.from_api(item)
        for item in _items(payload)
        if item.get("id")
    ]


def order_items_by_product(order_items: list[OrderItem]) -> dict[str, OrderItem]:
    """Map product (cycle) id -> billed order line."""
    mapping: dict[str, OrderItem] = {}

    for item in order_items:
        if item.product_id:
            mapping.setdefault(item.product_id, item)

    return mapping


def active_cycles_by_id(cycles: list[Cycle]) -> dict[str, Cycle]:
    """Map cycle id -> active cycle."""
    return {
        cycle.cycle_id: cycle
        for cycle in cycles
        if cycle.is_active and cycle.cycle_id
    }


def attach_cycles(
    machines: list[Machine],
    cycles: list[Cycle],
    order_items: list[OrderItem] | None = None,
) -> list[Machine]:
    """Attach this account's active cycles to the machines they run on.

    A machine that is busy carries ``availability.fulfillmentId``.  For the
    account's own cycles that value equals the cycle id, and cycles belonging
    to other users are simply absent from ``GET /cycles`` — so an exact match
    is what separates "your wash" from "somebody else's".

    When a machine reports no fulfillment id at all (for example right after
    a cycle was enabled, while availability still reads FREE) the machine id
    is used instead.
    """
    by_id = active_cycles_by_id(cycles)
    by_machine = active_cycles_by_machine(cycles)
    by_product = order_items_by_product(order_items or [])

    attached: list[Machine] = []

    for machine in machines:
        if machine.fulfillment_id:
            # An unmatched fulfillment id means somebody else is using it;
            # never fall back to the machine id in that case.
            cycle = by_id.get(machine.fulfillment_id)
        else:
            cycle = by_machine.get(machine.machine_id)

        machine = machine.with_cycle(cycle)

        if cycle is not None:
            machine = machine.with_order_item(by_product.get(cycle.cycle_id))

        attached.append(machine)

    return attached


def build_data(
    machines: list[Machine],
    cycles: list[Cycle],
    wallet: dict[str, Any] | None = None,
    order_items: list[OrderItem] | None = None,
) -> dict[str, Any]:
    """Map the API responses onto the structure used by the entities."""
    wallet = wallet or {}
    cycle_by_machine = active_cycles_by_machine(cycles)
    machines = attach_cycles(machines, cycles, order_items)

    washers = [machine for machine in machines if machine.is_washing_machine]
    dryers = [machine for machine in machines if machine.is_dryer]

    def _count(items: list[Machine], state: str) -> int:
        return sum(1 for machine in items if machine.availability_status == state)

    return {
        "machines": {machine.machine_id: machine for machine in machines},
        "machines_by_code": {machine.code: machine for machine in machines},
        "washing_machines": {
            "machines_status": {
                machine.code: machine.state for machine in washers
            },
            "available_machines": _count(washers, STATE_FREE),
            "occupied_machines": _count(washers, STATE_OCCUPIED),
            "total_machines": len(washers),
            "machines_data": washers,
        },
        "dryers": {
            "dryers_status": {
                machine.code: machine.state for machine in dryers
            },
            "available_dryers": _count(dryers, STATE_FREE),
            "occupied_dryers": _count(dryers, STATE_OCCUPIED),
            "total_dryers": len(dryers),
            "dryers_data": dryers,
        },
        "cycles": cycles,
        "active_cycles": cycle_by_machine,
        "own_machines": [
            machine for machine in machines if machine.is_own_cycle
        ],
        "balance": float(wallet.get("balance") or 0.0),
        "currency": wallet.get("currency") or "EUR",
        "wallet": {
            "available_balance": wallet.get("availableBalance"),
            "total_balance": wallet.get("totalBalance"),
            "authorized_balance": wallet.get("authorizedBalance"),
        },
    }
