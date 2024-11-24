"""Config flow for AppWash integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .api import AppWashAPI

class AppWashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AppWash."""

    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                api = AppWashAPI(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
                await api.async_login()
                
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=user_input
                )
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )
