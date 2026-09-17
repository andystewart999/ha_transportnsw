"""Config flow for Transport NSW Mk II integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from TransportNSWv2 import APIRateLimitExceeded, InvalidAPIKey, StopError, TripError

from homeassistant.config_entries import (
    SOURCE_IMPORT,
    # SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    STOP_TEST_ID,
    SUBENTRY_TYPE_JOURNEY,
    TFNSW_REGISTRATION,
)
from .helpers import check_stops
from .subentry_flow import JourneySubEntryFlowHandler

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input is correct
    Check that the API key is valid by calling the quick and easy 'stops' API with a hard-coded, known good station ID (Central Station)."""

    try:
        # Force a check and see if any errors are raised
        # stop_data = await hass.async_add_executor_job(
        #     check_stops, data[CONF_API_KEY], [STOP_TEST_ID]
        # )
        await hass.async_add_executor_job(
            check_stops, data[CONF_API_KEY], [STOP_TEST_ID]
        )

    # Testing simpler exception type
    except (InvalidAPIKey, APIRateLimitExceeded, StopError):
        raise

    except Exception as ex:
        raise StopError from ex


class TransportNSWConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Transport NSW Mk II"""

    VERSION = 3
    MINOR_VERSION = 0

    _input_data: dict[str, Any]

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        # Return subentries supported by this integration

        return {SUBENTRY_TYPE_JOURNEY: JourneySubEntryFlowHandler}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if self.source == SOURCE_IMPORT:
                # There won't have been a previous key to check against so create an empty 'previous key' variable
                # Also we don't need to do any validation as it's already been done elsewhere
                self._previous_key = ""
            else:
                # The form has been filled in and submitted, so process the data provided.
                try:
                    # Validate that the setup data is valid and if not handle errors
                    await validate_input(self.hass, user_input)

                except InvalidAPIKey:
                    errors["base"] = "invalidapikey"

                except APIRateLimitExceeded:
                    errors["base"] = "apiratelimitexceeded"

                except StopError:
                    errors["base"] = "stoperror"

                except TripError:
                    errors["base"] = "triperror"

                except Exception:
                    errors["base"] = "unknown"

            if not errors:
                # The API key is confirmed to be valid so set the entry unique ID based on the API key - we'll check for uniqueness shortly
                await self.async_set_unique_id(user_input[CONF_API_KEY])

                # It's a brand new config entry, but we still need to check for a unique id conflict
                self._abort_if_unique_id_configured()

                self._input_data = user_input

                # We're just creating a brand new config entry
                subentry_data = None

                # Actually create the config entry
                return self.async_create_entry(
                    title=f"Transport NSW Mk II ({user_input[CONF_API_KEY][-4:]})",
                    data=self._input_data,
                    subentries=subentry_data,
                )

        if user_input is None:
            user_input = {}
            self._previous_key = ""

        USER_DATA_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")
                ): str,
            }
        )

        description_placeholders = {"tfnsw_registration": TFNSW_REGISTRATION}

        # Show initial form
        return self.async_show_form(
            step_id="user",
            data_schema=USER_DATA_SCHEMA,
            errors=errors,
            last_step=True,
            description_placeholders=description_placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> TransportNSWOptionsFlowHandler:
        return TransportNSWOptionsFlowHandler()


class TransportNSWOptionsFlowHandler(OptionsFlowWithReload):
    """TransportNSW config flow options handler - we don't have an options
    change listener hence using OptionsFlowWithReload."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the options flow"""

        errors: dict[str, str] = {}

        OPTIONS_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=300,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # Show the options form
        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=OPTIONS_SCHEMA,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
