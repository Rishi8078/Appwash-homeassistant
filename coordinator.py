"""DataUpdateCoordinator for AppWash."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AppWashAPI,
    AppWashAuthError,
    AppWashError,
    AppWashRateLimitError,
)
from .const import DEFAULT_SCAN_INTERVAL
from .models import build_data

_LOGGER = logging.getLogger(__name__)


class AppWashDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AppWash data.

    A single update performs one ``GET /machines`` and one ``GET /cycles``
    request for the whole integration; entities only read the result.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: AppWashAPI,
        location_id: str | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="AppWash",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.location_id = location_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            if not self.location_id:
                self.location_id = await self.api.async_get_location_id()

            machines = await self.api.async_get_machines(self.location_id)
            cycles = await self.api.async_get_cycles(self.location_id)
            wallet = await self.api.async_get_wallet()
        except AppWashAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AppWashRateLimitError as err:
            raise UpdateFailed(f"AppWash API rate limited: {err}") from err
        except AppWashError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:  # pylint: disable=broad-except
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return build_data(machines, cycles, wallet)
