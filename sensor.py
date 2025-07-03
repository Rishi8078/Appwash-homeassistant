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
    
    # Add individual washing machine sensors using optimized data structure
    machines_status = coordinator.data["washing_machines"]["machines_status"]
    for machine_name in machines_status.keys():
        sensors.append(AppWashIndividualWashingMachineSensor(
            coordinator, 
            machine_name
        ))
    
    # Add individual dryer sensors using optimized data structure
    dryers_status = coordinator.data["dryers"]["dryers_status"]
    for dryer_name in dryers_status.keys():
        sensors.append(AppWashIndividualDryerSensor(
            coordinator, 
            dryer_name
        ))
    
    # Add aggregate sensors for better overview
    sensors.extend([
        AppWashWashingMachinesSummary(coordinator),
        AppWashDryersSummary(coordinator),
        AppWashBalanceSensor(coordinator)
    ])

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

class AppWashWashingMachinesSummary(CoordinatorEntity, SensorEntity):
    """Summary sensor for all washing machines."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Washing Machines Available"
        self._attr_unique_id = "appwash_washing_machines_available"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return available washing machines count."""
        return self.coordinator.data["washing_machines"]["available_machines"]

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        data = self.coordinator.data["washing_machines"]
        return {
            "available": data["available_machines"],
            "occupied": data["occupied_machines"],
            "total": data["total_machines"]
        }

class AppWashDryersSummary(CoordinatorEntity, SensorEntity):
    """Summary sensor for all dryers."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Dryers Available"
        self._attr_unique_id = "appwash_dryers_available"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return available dryers count."""
        return self.coordinator.data["dryers"]["available_dryers"]

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        data = self.coordinator.data["dryers"]
        return {
            "available": data["available_dryers"],
            "occupied": data["occupied_dryers"],
            "total": data.get("total_dryers", 0)
        }

class AppWashBalanceSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AppWash balance sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "AppWash Balance"
        self._attr_unique_id = "appwash_balance"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["balance"]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "EUR"
