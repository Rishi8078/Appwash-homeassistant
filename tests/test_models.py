"""Tests for the normalized AppWash data model."""
from __future__ import annotations

from datetime import datetime, timezone

from appwash.models import (
    Cycle,
    Machine,
    active_cycles_by_machine,
    build_data,
    parse_cycles,
    parse_machines,
    parse_timestamp,
)

from fixtures import (
    ACTIVE_CYCLE,
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

    assert [machine.code for machine in machines] == ["46084", "46115"]


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

    assert washers["machines_status"] == {"46084": "OCCUPIED"}
    assert washers["available_machines"] == 0
    assert washers["occupied_machines"] == 1
    assert washers["total_machines"] == 1
    assert dryers["dryers_status"] == {"46115": "FREE"}
    assert dryers["available_dryers"] == 1
    assert dryers["occupied_dryers"] == 0
    assert data["balance"] == 3.0
    assert data["currency"] == "EUR"

    washer = washers["machines_data"][0]

    assert washer.cycle is not None
    assert washer.as_attributes()["cycle_id"] == FULFILLMENT_ID
    assert washer.as_attributes()["cycle_order_id"] == ORDER_ID

    dryer = dryers["dryers_data"][0]

    assert dryer.cycle is None
    assert "cycle_id" not in dryer.as_attributes()


def test_build_data_without_wallet():
    data = build_data(parse_machines(MACHINES_RESPONSE), [], None)

    assert data["balance"] == 0.0
    assert data["currency"] == "EUR"
