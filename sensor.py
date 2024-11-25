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

    sensors = []
    
    # Add individual washing machine sensors
    for machine in coordinator.data["washing_machines"]["machines_data"]:
        sensors.append(AppWashIndividualWashingMachineSensor(
            coordinator, 
            machine["connectorName"]
        ))
    
    # Add individual dryer sensors
    for dryer in coordinator.data["dryers"]["dryers_data"]:
        sensors.append(AppWashIndividualDryerSensor(
            coordinator, 
            dryer["connectorName"]
        ))
    
    # Add balance sensor
    sensors.append(AppWashBalanceSensor(coordinator))

    async_add_entities(sensors)

class AppWashIndividualWashingMachineSensor(CoordinatorEntity, SensorEntity):
    """Representation of an individual AppWash washing machine sensor."""

    def __init__(self, coordinator, machine_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._machine_id = machine_id
        self._attr_name = f"Washing Machine {machine_id}"
        self._attr_unique_id = f"appwash_washing_machine_{machine_id}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["washing_machines"]["machines_status"].get(self._machine_id, "unknown")

class AppWashIndividualDryerSensor(CoordinatorEntity, SensorEntity):
    """Representation of an individual AppWash dryer sensor."""

    def __init__(self, coordinator, dryer_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._dryer_id = dryer_id
        self._attr_name = f"Dryer {dryer_id}"
        self._attr_unique_id = f"appwash_dryer_{dryer_id}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["dryers"]["dryers_status"].get(self._dryer_id, "unknown")


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
