"""Tests for the normalized AppWash data model."""
from __future__ import annotations

from datetime import datetime, timezone

from appwash.models import (
    Cycle,
    OrderItem,
    Machine,
    active_cycles_by_id,
    active_cycles_by_machine,
    attach_cycles,
    build_data,
    parse_cycles,
    parse_machines,
    parse_order_items,
    parse_timestamp,
)

from fixtures import (
    ACTIVE_CYCLE,
    ACTIVE_ORDER_ITEM,
    ORDER_ITEMS_RESPONSE,
    OTHER_FULFILLMENT_ID,
    OTHER_MACHINE_ID,
    OTHER_OCCUPIED_MACHINE,
    CYCLES_RESPONSE,
    FREE_MACHINE,
    FREE_MACHINE_ID,
    FULFILLMENT_ID,
    LOCATION_ID,
    MACHINES_RESPONSE,
    OCCUPIED_MACHINE,
    OCCUPIED_MACHINE_ID,
    ORDER_ID,
    STOPPED_CYCLE,
    WALLET_RESPONSE,
)


def test_parse_occupied_machine():
    machine = Machine.from_api(OCCUPIED_MACHINE)

    assert machine.machine_id == OCCUPIED_MACHINE_ID
    assert machine.code == "46084"
    assert machine.name == "46084"
    assert machine.product_group == "WM"
    assert machine.location_id == LOCATION_ID
    assert machine.availability_status == "OCCUPIED"
    assert machine.is_occupied is True
    assert machine.is_free is False
    assert machine.is_washing_machine is True
    assert machine.is_dryer is False
    assert machine.status_since == "2026-08-28T12:39:29.705243Z"
    assert machine.cycle_price == 3.0
    assert machine.currency == "EUR"


def test_parse_free_machine_with_null_status_since():
    machine = Machine.from_api(FREE_MACHINE)

    assert machine.machine_id == FREE_MACHINE_ID
    assert machine.availability_status == "FREE"
    assert machine.is_free is True
    assert machine.status_since is None
    assert machine.is_dryer is True


def test_machine_with_fulfillment_id():
    assert Machine.from_api(OCCUPIED_MACHINE).fulfillment_id == FULFILLMENT_ID


def test_machine_without_fulfillment_id():
    assert Machine.from_api(FREE_MACHINE).fulfillment_id is None


def test_machine_checked_window():
    machine = Machine.from_api(OCCUPIED_MACHINE)

    assert machine.checked_at == "2026-08-28T13:24:14.723753417Z"
    assert machine.checked_from == "2026-08-28T13:24:14.7127584Z"
    assert machine.checked_until == "2026-08-28T15:24:14.7127584Z"


def test_machine_without_availability_block():
    machine = Machine.from_api({"id": "x", "code": "1", "productGroup": "WM"})

    assert machine.availability_status == "UNKNOWN"
    assert machine.is_free is False
    assert machine.is_occupied is False
    assert machine.checked_until is None
    assert machine.estimated_end is None
    assert machine.remaining_minutes() is None


def test_estimated_end_and_remaining_minutes():
    machine = Machine.from_api(OCCUPIED_MACHINE)
    now = datetime(2026, 8, 28, 13, 39, 29, tzinfo=timezone.utc)

    assert machine.estimated_end == parse_timestamp(
        "2026-08-28T14:39:29.705243Z"
    )
    assert machine.remaining_minutes(now) == 60


def test_free_machine_has_no_estimated_end():
    assert Machine.from_api(FREE_MACHINE).estimated_end is None


def test_parse_timestamp_handles_nanoseconds_and_none():
    parsed = parse_timestamp("2026-08-28T13:24:14.723753417Z")

    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.year == 2026
    assert parse_timestamp(None) is None
    assert parse_timestamp("not a date") is None


def test_machine_attributes_contain_documented_keys():
    machine = Machine.from_api(OCCUPIED_MACHINE)
    attributes = machine.as_attributes()

    for key in (
        "machine_code",
        "machine_name",
        "machine_id",
        "product_group",
        "availability_status",
        "status_since",
        "fulfillment_id",
        "checked_at",
        "checked_from",
        "checked_until",
        "cycle_price",
        "currency",
        "additional_info",
    ):
        assert key in attributes

    assert attributes["machine_code"] == "46084"
    assert attributes["availability_status"] == "OCCUPIED"


def test_parse_machines_collection():
    machines = parse_machines(MACHINES_RESPONSE)

    assert [machine.code for machine in machines] == ["46084", "46115", "46113"]


def test_parse_machines_ignores_garbage():
    assert parse_machines({}) == []
    assert parse_machines(None) == []
    assert parse_machines({"items": [{"code": "no id"}]}) == []


def test_parse_enabled_cycle():
    cycle = Cycle.from_api(ACTIVE_CYCLE)

    assert cycle.cycle_id == FULFILLMENT_ID
    assert cycle.machine_id == OCCUPIED_MACHINE_ID
    assert cycle.machine_code == "46084"
    assert cycle.location_id == LOCATION_ID
    assert cycle.product_type == "FIX_CYCLE_WASHING"
    assert cycle.product_kind == "CYCLE"
    assert cycle.order_id == ORDER_ID
    assert cycle.status == "ENABLED"
    assert cycle.termination_reason is None
    assert cycle.enabled_at == "2026-08-28T12:39:29.705243Z"
    assert cycle.stopped_at is None
    assert cycle.is_active is True


def test_parse_stopped_cycle():
    cycle = Cycle.from_api(STOPPED_CYCLE)

    assert cycle.is_active is False
    assert cycle.stopped_at == "2026-08-28T13:39:29.705243Z"
    assert cycle.termination_reason == "COMPLETED"


def test_active_cycles_are_mapped_by_machine():
    cycles = parse_cycles(CYCLES_RESPONSE)
    mapping = active_cycles_by_machine(cycles)

    assert set(mapping) == {OCCUPIED_MACHINE_ID}
    assert mapping[OCCUPIED_MACHINE_ID].cycle_id == FULFILLMENT_ID


def test_machine_availability_fulfillment_matches_active_cycle():
    machine = Machine.from_api(OCCUPIED_MACHINE)
    cycle = Cycle.from_api(ACTIVE_CYCLE)

    assert machine.fulfillment_id == cycle.cycle_id


def test_build_data_groups_machines_and_attaches_cycles():
    data = build_data(
        parse_machines(MACHINES_RESPONSE),
        parse_cycles(CYCLES_RESPONSE),
        WALLET_RESPONSE,
    )

    washers = data["washing_machines"]
    dryers = data["dryers"]

    assert washers["machines_status"] == {"46084": "YOUR_CYCLE"}
    assert washers["available_machines"] == 0
    assert washers["occupied_machines"] == 1
    assert washers["total_machines"] == 1
    assert dryers["dryers_status"] == {"46115": "FREE", "46113": "OCCUPIED"}
    assert dryers["available_dryers"] == 1
    assert dryers["occupied_dryers"] == 1
    assert data["balance"] == 3.0
    assert data["currency"] == "EUR"

    washer = washers["machines_data"][0]

    assert washer.cycle is not None
    assert washer.as_attributes()["cycle_id"] == FULFILLMENT_ID
    assert washer.as_attributes()["cycle_order_id"] == ORDER_ID

    dryer = dryers["dryers_data"][0]

    assert dryer.cycle is None
    assert "cycle_id" not in dryer.as_attributes()
    assert data["own_machines"] == [washer]


def test_build_data_without_wallet():
    data = build_data(parse_machines(MACHINES_RESPONSE), [], None)

    assert data["balance"] == 0.0
    assert data["currency"] == "EUR"


# ----------------------------------------------------------------------
# Cycle ownership
# ----------------------------------------------------------------------


def _attached(machine_payload, cycle_payloads=(ACTIVE_CYCLE,), order_items=()):
    machines = attach_cycles(
        [Machine.from_api(machine_payload)],
        [Cycle.from_api(payload) for payload in cycle_payloads],
        [OrderItem.from_api(payload) for payload in order_items],
    )

    return machines[0]


def test_own_occupancy_is_reported_as_your_cycle():
    machine = _attached(OCCUPIED_MACHINE)

    assert machine.is_own_cycle is True
    assert machine.occupied_by == "you"
    assert machine.state == "YOUR_CYCLE"
    # The raw API value is still available untouched.
    assert machine.availability_status == "OCCUPIED"


def test_someone_elses_occupancy_stays_occupied():
    machine = _attached(OTHER_OCCUPIED_MACHINE)

    assert machine.cycle is None
    assert machine.is_own_cycle is False
    assert machine.occupied_by == "other"
    assert machine.state == "OCCUPIED"


def test_free_machine_has_no_owner():
    machine = _attached(FREE_MACHINE)

    assert machine.is_own_cycle is False
    assert machine.occupied_by is None
    assert machine.state == "FREE"


def test_ownership_requires_a_matching_fulfillment_id():
    """A cycle on the same machine does not make a foreign occupancy yours."""
    stale = dict(ACTIVE_CYCLE, machine=dict(ACTIVE_CYCLE["machine"], id=OTHER_MACHINE_ID))

    machine = _attached(OTHER_OCCUPIED_MACHINE, [stale])

    assert machine.cycle is None
    assert machine.state == "OCCUPIED"
    assert machine.occupied_by == "other"


def test_stopped_cycle_does_not_claim_a_machine():
    machine = _attached(OCCUPIED_MACHINE, [STOPPED_CYCLE])

    assert machine.cycle is None
    assert machine.is_own_cycle is False
    assert machine.state == "OCCUPIED"


def test_free_machine_with_an_own_cycle_keeps_the_free_state():
    """Right after enabling a cycle, availability can still read FREE."""
    payload = dict(FREE_MACHINE)
    payload["id"] = OCCUPIED_MACHINE_ID
    payload["availability"] = dict(
        FREE_MACHINE["availability"], subjectId=OCCUPIED_MACHINE_ID
    )

    machine = _attached(payload)

    assert machine.cycle is not None
    assert machine.is_own_cycle is True
    # Availability is the API's truth; it is never overridden upwards.
    assert machine.state == "FREE"
    assert machine.occupied_by is None


def test_unknown_machine_state_is_passed_through():
    machine = _attached({"id": "x", "code": "1", "productGroup": "WM"})

    assert machine.state == "UNKNOWN"
    assert machine.occupied_by is None


def test_active_cycles_by_id_ignores_stopped_cycles():
    mapping = active_cycles_by_id(parse_cycles(CYCLES_RESPONSE))

    assert set(mapping) == {FULFILLMENT_ID}


def test_ownership_attributes_are_exposed():
    attributes = _attached(OCCUPIED_MACHINE).as_attributes()

    assert attributes["is_own_cycle"] is True
    assert attributes["occupied_by"] == "you"
    assert attributes["availability_status"] == "OCCUPIED"

    attributes = _attached(OTHER_OCCUPIED_MACHINE).as_attributes()

    assert attributes["is_own_cycle"] is False
    assert attributes["occupied_by"] == "other"
    assert attributes["fulfillment_id"] == OTHER_FULFILLMENT_ID


# ----------------------------------------------------------------------
# Progress and billing attributes
# ----------------------------------------------------------------------


def test_occupancy_window_progress():
    machine = Machine.from_api(OCCUPIED_MACHINE)
    # Window runs 12:39:29 -> 14:39:29; sample it 30 minutes in.
    now = datetime(2026, 8, 28, 13, 9, 29, tzinfo=timezone.utc)

    assert machine.cycle_duration_minutes == 120
    assert machine.elapsed_minutes(now) == 30
    assert machine.progress_percent(now) == 25
    assert machine.remaining_minutes(now) == 90


def test_progress_is_clamped_past_the_window():
    machine = Machine.from_api(OCCUPIED_MACHINE)
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)

    assert machine.progress_percent(now) == 100
    assert machine.remaining_minutes(now) == 0


def test_free_machine_has_no_progress():
    machine = Machine.from_api(FREE_MACHINE)

    assert machine.occupied_since is None
    assert machine.cycle_duration_minutes is None
    assert machine.elapsed_minutes() is None
    assert machine.progress_percent() is None


def test_price_type_is_exposed():
    assert Machine.from_api(OCCUPIED_MACHINE).as_attributes()["price_type"] == (
        "FIX_PRICE"
    )


def test_parse_order_items():
    items = parse_order_items(ORDER_ITEMS_RESPONSE)

    assert len(items) == 2
    assert items[1].product_id == FULFILLMENT_ID
    assert items[1].fulfillment_status == "FULFILLING"
    assert items[1].gross_total_amount == 3.0
    assert items[1].order_id == ORDER_ID


def test_order_item_is_attached_to_the_machine_running_the_cycle():
    machine = _attached(OCCUPIED_MACHINE, order_items=[ACTIVE_ORDER_ITEM])
    attributes = machine.as_attributes()

    assert machine.order_item is not None
    assert attributes["cycle_fulfillment_status"] == "FULFILLING"
    assert attributes["cycle_order_status"] == "BOOKED"
    assert attributes["cycle_paid_amount"] == 3.0
    assert attributes["cycle_description"] == "Machine: 46084"


def test_order_items_are_not_attached_without_a_cycle():
    machine = _attached(OTHER_OCCUPIED_MACHINE, order_items=[ACTIVE_ORDER_ITEM])

    assert machine.order_item is None
    assert "cycle_fulfillment_status" not in machine.as_attributes()


def test_build_data_exposes_the_rest_of_the_wallet():
    data = build_data(
        parse_machines(MACHINES_RESPONSE),
        parse_cycles(CYCLES_RESPONSE),
        WALLET_RESPONSE,
        parse_order_items(ORDER_ITEMS_RESPONSE),
    )

    assert data["wallet"] == {
        "available_balance": 3.0,
        "total_balance": 3.0,
        "authorized_balance": 0.0,
    }

    washer = data["washing_machines"]["machines_data"][0]

    assert washer.as_attributes()["cycle_fulfillment_status"] == "FULFILLING"
