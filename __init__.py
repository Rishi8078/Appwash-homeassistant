"""The AppWash integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AppWashAPI, AppWashAuthError, AppWashError
from .const import CONF_EMAIL, CONF_LOCATION_ID, CONF_PASSWORD, DOMAIN
from .coordinator import AppWashDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AppWash from a config entry."""
    location_id = entry.options.get(
        CONF_LOCATION_ID, entry.data.get(CONF_LOCATION_ID)
    )

    api = AppWashAPI(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
        location_id=location_id,
    )

    try:
        await api.async_login()
    except AppWashAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except AppWashError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = AppWashDataUpdateCoordinator(hass, api, location_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()
    return unload_ok
