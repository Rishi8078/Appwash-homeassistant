"""The AppWash integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import AppWashDataUpdateCoordinator
from .api import AppWashAPI

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AppWash from a config entry with optimized startup."""
    api = AppWashAPI(entry.data["email"], entry.data["password"])
    
    # Defer login to first data fetch to speed up startup
    coordinator = AppWashDataUpdateCoordinator(hass, api)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Start background refresh without blocking startup
    await coordinator.async_config_entry_first_refresh()
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Properly close the API session to free resources
        await coordinator.api.close()
    return unload_ok
