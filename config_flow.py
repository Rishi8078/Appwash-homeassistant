"""Config flow for AppWash integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AppWashAPI, AppWashAuthError, AppWashError
from .const import (
    CONF_EMAIL,
    CONF_LOCATION_ID,
    CONF_LOCATION_NAME,
    CONF_PASSWORD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class AppWashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AppWash."""

    VERSION = 1

    async def _async_validate(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Log in and resolve the location of the account."""
        api = AppWashAPI(
            user_input[CONF_EMAIL],
            user_input[CONF_PASSWORD],
            session=async_get_clientsession(self.hass),
        )

        await api.async_login()
        user = await api.async_get_user()
        location = user.get("preferredLocation") or {}

        return {
            **user_input,
            CONF_LOCATION_ID: location.get("id"),
            CONF_LOCATION_NAME: location.get("name"),
        }

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                data = await self._async_validate(user_input)
            except AppWashAuthError:
                errors["base"] = "invalid_auth"
            except AppWashError as err:
                _LOGGER.debug("Cannot connect to AppWash: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error setting up AppWash")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Handle re-authentication after the credentials stopped working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for new credentials."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None and entry is not None:
            credentials = {
                CONF_EMAIL: entry.data[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }

            try:
                data = await self._async_validate(credentials)
            except AppWashAuthError:
                errors["base"] = "invalid_auth"
            except AppWashError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, **data}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "AppWashOptionsFlow":
        """Return the options flow."""
        return AppWashOptionsFlow()


class AppWashOptionsFlow(config_entries.OptionsFlow):
    """Allow overriding the location that is polled."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            location_id = (user_input.get(CONF_LOCATION_ID) or "").strip()

            return self.async_create_entry(
                title="",
                data=(
                    {CONF_LOCATION_ID: location_id} if location_id else {}
                ),
            )

        current = self.config_entry.options.get(
            CONF_LOCATION_ID,
            self.config_entry.data.get(CONF_LOCATION_ID, ""),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LOCATION_ID, default=current or ""
                    ): str,
                }
            ),
        )
