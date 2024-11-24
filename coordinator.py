"""DataUpdateCoordinator for AppWash."""
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DEFAULT_SCAN_INTERVAL
from .api import AppWashAPI

_LOGGER = logging.getLogger(__name__)

class AppWashDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AppWash data."""

    def __init__(self, hass: HomeAssistant, api: AppWashAPI) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="AppWash",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            data = {}
            data["washing_machines"] = await self.api.async_get_washing_machines()
            data["dryers"] = await self.api.async_get_dryers()
            data["balance"] = await self.api.async_get_balance()
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
