"""DataUpdateCoordinator for AppWash."""
import asyncio
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
        """Fetch data from API with parallel calls for improved performance."""
        try:
            # Ensure we're logged in before making API calls
            if not self.api._token:
                await self.api.async_login()
                
            # Execute all API calls in parallel to reduce total update time
            washing_task = self.api.async_get_washing_machines()
            dryers_task = self.api.async_get_dryers()
            balance_task = self.api.async_get_balance()
            
            washing_machines, dryers, balance = await asyncio.gather(
                washing_task, dryers_task, balance_task
            )
            
            return {
                "washing_machines": washing_machines,
                "dryers": dryers,
                "balance": balance
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
