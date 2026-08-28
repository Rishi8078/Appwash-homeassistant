"""Support for AppWash sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION_NAME, DOMAIN, STATE_UNKNOWN
from .coordinator import AppWashDataUpdateCoordinator
from .models import Machine


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AppWash sensors based on a config entry."""
    coordinator: AppWashDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = []

    # Add individual washing machine sensors
    for machine in coordinator.data["washing_machines"]["machines_data"]:
        sensors.append(
            AppWashIndividualWashingMachineSensor(coordinator, machine.code, entry)
        )

    # Add individual dryer sensors
    for machine in coordinator.data["dryers"]["dryers_data"]:
        sensors.append(
            AppWashIndividualDryerSensor(coordinator, machine.code, entry)
        )

    # Add balance sensor
    sensors.append(AppWashBalanceSensor(coordinator, entry))

    async_add_entities(sensors)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device all AppWash entities belong to."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_LOCATION_NAME) or "AppWash",
        manufacturer="Miele",
        model="AppWash",
    )


class AppWashMachineSensor(CoordinatorEntity, SensorEntity):
    """Common behaviour for machine sensors."""

    _key = "washing_machines"
    _data_key = "machines_data"

    def __init__(
        self,
        coordinator: AppWashDataUpdateCoordinator,
        machine_code: str,
        entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._machine_code = machine_code

        if entry is not None:
            self._attr_device_info = _device_info(entry)

    @property
    def _machine(self) -> Machine | None:
        """Return the machine this sensor represents."""
        data = self.coordinator.data or {}

        for machine in data.get(self._key, {}).get(self._data_key, []):
            if machine.code == self._machine_code:
                return machine

        return None

    @property
    def available(self) -> bool:
        """Return True if the machine is still reported by the API."""
        return super().available and self._machine is not None

    @property
    def native_value(self) -> str:
        """Return the availability state of the machine."""
        machine = self._machine

        if machine is None:
            return STATE_UNKNOWN

        return machine.availability_status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the machine (and active cycle) details."""
        machine = self._machine

        if machine is None:
            return {}

        return machine.as_attributes()


class AppWashIndividualWashingMachineSensor(AppWashMachineSensor):
    """Representation of an individual AppWash washing machine sensor."""

    _key = "washing_machines"
    _data_key = "machines_data"
    _attr_icon = "mdi:washing-machine"

    def __init__(self, coordinator, machine_id, entry=None):
        """Initialize the sensor."""
        super().__init__(coordinator, machine_id, entry)
        self._attr_name = f"Washing Machine {machine_id}"
        self._attr_unique_id = f"appwash_washing_machine_{machine_id}"


class AppWashIndividualDryerSensor(AppWashMachineSensor):
    """Representation of an individual AppWash dryer sensor."""

    _key = "dryers"
    _data_key = "dryers_data"
    _attr_icon = "mdi:tumble-dryer"

    def __init__(self, coordinator, dryer_id, entry=None):
        """Initialize the sensor."""
        super().__init__(coordinator, dryer_id, entry)
        self._attr_name = f"Dryer {dryer_id}"
        self._attr_unique_id = f"appwash_dryer_{dryer_id}"


class AppWashBalanceSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AppWash balance sensor."""

    _attr_icon = "mdi:wallet"

    def __init__(self, coordinator, entry: ConfigEntry | None = None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Balance"
        self._attr_unique_id = "appwash_balance"
        self._attr_state_class = SensorStateClass.MEASUREMENT

        if entry is not None:
            self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float | None:
        """Return the wallet balance."""
        return (self.coordinator.data or {}).get("balance")

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return (self.coordinator.data or {}).get("currency") or "EUR"
