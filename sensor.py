"""Support for AppWash sensors."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_AVAILABLE, ATTR_OCCUPIED, ATTR_STATUS
from .coordinator import AppWashDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AppWash sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        AppWashWashingMachineSensor(coordinator),
        AppWashDryerSensor(coordinator),
        AppWashBalanceSensor(coordinator),
    ]

    async_add_entities(sensors)

class AppWashWashingMachineSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AppWash washing machine sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Washing Machines"
        self._attr_unique_id = f"appwash_washing_machines"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["washing_machines"]["available_machines"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_AVAILABLE: self.coordinator.data["washing_machines"]["available_machines"],
            ATTR_OCCUPIED: self.coordinator.data["washing_machines"]["occupied_machines"],
            ATTR_STATUS: self.coordinator.data["washing_machines"]["machines_status"]
        }

class AppWashDryerSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AppWash dryer sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Dryers"
        self._attr_unique_id = f"appwash_dryers"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["dryers"]["available_dryers"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_AVAILABLE: self.coordinator.data["dryers"]["available_dryers"],
            ATTR_OCCUPIED: self.coordinator.data["dryers"]["occupied_dryers"],
            ATTR_STATUS: self.coordinator.data["dryers"]["dryers_status"]
        }

class AppWashBalanceSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AppWash balance sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Balance"
        self._attr_unique_id = f"appwash_balance"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["balance"]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "EUR"
