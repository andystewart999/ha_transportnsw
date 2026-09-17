"""The Transport NSW Mk II integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

# from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

# from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION
from .coordinator import (
    TransportNSWConfigEntry,
    TransportNSWCoordinator,
    TransportNSWRuntimeData,
)

_LOGGER = logging.getLogger(__name__)

### Temporarily removed to simplify initial core submission review - will be re-added in a future PR
PLATFORMS: list[Platform] = [Platform.SENSOR]  # , Platform.DEVICE_TRACKER]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config_entry: TransportNSWConfigEntry):

    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: TransportNSWConfigEntry
) -> bool:
    """Set up the ha_transportnsw integration from a config entry."""

    try:
        # Initialise the persistent api_data storage
        api_store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{config_entry.entry_id}")
        _LOGGER.debug(f"Initialised persistent storage for {config_entry.title}")

    except Exception as ex:
        # This isn't ideal but we can carry on - but ideally we'd be able to count and store API usage.
        _LOGGER.warning(f"Error initialising persistent storage: {ex}")

    try:
        # Initialise the coordinator that manages data updates
        coordinator = TransportNSWCoordinator(hass, config_entry)

        # Add the coordinator and API store to config runtime data to make
        # them accessible throughout the integration
        config_entry.runtime_data = TransportNSWRuntimeData(
            coordinator,
            api_store,
        )

        # Initiate the coordinator
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug(f"Initialised coordinator for {config_entry.title}")

    except Exception as ex:
        # This is a fatal error
        _LOGGER.error(f"Error initialising coordinator: {ex}")
        return False

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Return true to denote a successful setup
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: TransportNSWConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading entry {config_entry.title}")

    ### Temporarily removed to simplify initial core submission review - will be re-added in a future PR
    # try:
    #     """Unregister frontend modules during unload"""
    #     module_register = JSModuleRegistration(hass)
    #     await module_register.async_unregister()

    #     # Make a note that the frontend has been unloaded
    #     hass.data[DOMAIN]["frontend_loaded"] = False

    # except Exception as ex:
    #     _LOGGER.error(f"Error unloading frontend module: {ex}")

    # Unload platforms and return result
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_remove_entry(
    hass: HomeAssistant, config_entry: TransportNSWConfigEntry
) -> None:
    """Handle removal of an entry - clean up the api_data storage file."""
    try:
        await config_entry.runtime_data.api_store.async_remove()

    finally:
        _LOGGER.debug(f"Removed entry {config_entry.title}")
