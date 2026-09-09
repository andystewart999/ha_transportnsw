"""The Transport NSW Mk II integration."""

from __future__ import annotations

import logging
from collections import defaultdict

import voluptuous as vol
from TransportNSWv2 import InvalidAPIKey, StopError

from homeassistant import config_entries
from homeassistant.components import persistent_notification, websocket_api
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import EVENT_HOMEASSISTANT_STARTED, CoreState, HomeAssistant

# from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

# from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.storage import Store

from .const import (
    CONF_ALERT_SEVERITY,
    CONF_ALERT_TYPES,
    CONF_ALERTS_SENSOR,
    CONF_DESTINATION_DEVICE_TRACKER,
    CONF_DESTINATION_ID,
    CONF_DESTINATION_NAME,
    CONF_DESTINATION_TRANSPORT_TYPE,
    CONF_END_TIME,
    CONF_FIRST_LEG_DEVICE_TRACKER,
    CONF_INCLUDE_REALTIME_LOCATION,
    CONF_LAST_LEG_DEVICE_TRACKER,
    CONF_MAX_CHANGES,
    CONF_ORIGIN_DEVICE_TRACKER,
    CONF_ORIGIN_ID,
    CONF_ORIGIN_NAME,
    CONF_ORIGIN_TRANSPORT_TYPE,
    CONF_RETURN_INFO,
    CONF_ROUTE_FILTER,
    CONF_RUN_FILTER,
    CONF_SENSOR_CREATION,
    CONF_START_TIME,
    CONF_TRIP_WAIT_TIME,
    CONF_TRIPS_TO_CREATE,
    DEFAULT_DESTINATION_DEVICE_TRACKER,
    DEFAULT_END_TIME,
    DEFAULT_FIRST_LEG_DEVICE_TRACKER,
    DEFAULT_LAST_LEG_DEVICE_TRACKER,
    DEFAULT_MAX_CHANGES,
    DEFAULT_ORIGIN_DEVICE_TRACKER,
    DEFAULT_RUN_FILTER,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_START_TIME,
    DOMAIN,
    INTEGRATION_VERSION,
    STORAGE_VERSION,
    SUBENTRY_TYPE_JOURNEY,
)
from .coordinator import (
    TransportNSWConfigEntry,
    TransportNSWCoordinator,
    TransportNSWRuntimeData,
)
from .helpers import (
    check_stops,
    delete_legacy_storage,
    get_optional_sensors,
    set_optional_sensors,
)
from .www import JSModuleRegistration

_LOGGER = logging.getLogger(__name__)

### Temporarily removed to simplify initial core submission review - will be re-added in a future PR
PLATFORMS: list[Platform] = [Platform.SENSOR] #, Platform.DEVICE_TRACKER]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: TransportNSWConfigEntry
):
    """ Schema migrations.""""

    if config_entry.version > 3:
        # This means the user has downgraded from a future version
        return False

    new_data = {**config_entry.data}
    new_options = {**config_entry.options}

    if config_entry.version < 2:
        # Migrate to version 2
        _LOGGER.info("Interim migration of configuration to version 2")

        # Migrate all subentries to the version 2 data schema
        for subentry in config_entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_JOURNEY:
                new_subentry_data = {**subentry.data}

                # We need to move a few entries around and create a whole new 'device_trackers' section
                # Cater for missing options by using .get() although theoretically that's impossible
                first_leg_device_tracker = new_subentry_data["origin_sensors"].get(
                    CONF_FIRST_LEG_DEVICE_TRACKER, DEFAULT_FIRST_LEG_DEVICE_TRACKER
                )
                last_leg_device_tracker = new_subentry_data["destination_sensors"].get(
                    CONF_LAST_LEG_DEVICE_TRACKER, DEFAULT_LAST_LEG_DEVICE_TRACKER
                )

                # Create the new sensor dictionary
                new_options = {
                    "device_trackers": {
                        CONF_FIRST_LEG_DEVICE_TRACKER: first_leg_device_tracker,
                        CONF_LAST_LEG_DEVICE_TRACKER: last_leg_device_tracker,
                        CONF_ORIGIN_DEVICE_TRACKER: DEFAULT_ORIGIN_DEVICE_TRACKER,
                        CONF_DESTINATION_DEVICE_TRACKER: DEFAULT_DESTINATION_DEVICE_TRACKER,
                    }
                }

                new_subentry_data.update(new_options)

                # Tidy up the old data a bit
                if CONF_FIRST_LEG_DEVICE_TRACKER in new_subentry_data["origin_sensors"]:
                    del new_subentry_data["origin_sensors"][
                        CONF_FIRST_LEG_DEVICE_TRACKER
                    ]

                if (
                    CONF_LAST_LEG_DEVICE_TRACKER
                    in new_subentry_data["destination_sensors"]
                ):
                    del new_subentry_data["destination_sensors"][
                        CONF_LAST_LEG_DEVICE_TRACKER
                    ]

                # Update the subentry
                hass.config_entries.async_update_subentry(
                    config_entry, subentry, data=new_subentry_data
                )

    if config_entry.version < 3:
        # Migrate to version 3
        _LOGGER.info("Migrating configuration to version 3")

        # Move CONF_SCAN_INTERVAL from .data to .options
        if CONF_SCAN_INTERVAL in new_data:
            new_options[CONF_SCAN_INTERVAL] = new_data[CONF_SCAN_INTERVAL]
            del new_data[CONF_SCAN_INTERVAL]
        else:
            new_options[CONF_SCAN_INTERVAL] = new_options.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            )

        # Migrate all subentries to the version 3 data schema
        for subentry in config_entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_JOURNEY:
                new_subentry_data = {**subentry.data}

                # Convert *_transport_type to a list of strings
                new_subentry_data[CONF_ORIGIN_TRANSPORT_TYPE] = [
                    str(transport_type)
                    for transport_type in new_subentry_data[CONF_ORIGIN_TRANSPORT_TYPE]
                ]
                new_subentry_data[CONF_DESTINATION_TRANSPORT_TYPE] = [
                    str(transport_type)
                    for transport_type in new_subentry_data[
                        CONF_DESTINATION_TRANSPORT_TYPE
                    ]
                ]

                # Make sure that recent options such as CONF_RUN_FILTER and CONF_MAX_CHANGES are present
                if CONF_RUN_FILTER not in new_subentry_data:
                    new_subentry_data[CONF_RUN_FILTER] = DEFAULT_RUN_FILTER

                if CONF_MAX_CHANGES not in new_subentry_data:
                    new_subentry_data[CONF_MAX_CHANGES] = DEFAULT_MAX_CHANGES

                if CONF_START_TIME not in new_subentry_data:
                    new_subentry_data[CONF_START_TIME] = DEFAULT_START_TIME

                if CONF_END_TIME not in new_subentry_data:
                    new_subentry_data[CONF_END_TIME] = DEFAULT_END_TIME

                # Update the subentry
                hass.config_entries.async_update_subentry(
                    config_entry, subentry, data=new_subentry_data
                )

        # The last step for the migration to version 3 - delete the legacy api usage storage file
        await hass.async_add_executor_job(
            delete_legacy_storage,
            hass.config.config_dir,
            config_entry,
        )

    # Finally, update the config entry itself - just the schema version number
    hass.config_entries.async_update_entry(
        config_entry, data=new_data, options=new_options, minor_version=0, version=3
    )

    _LOGGER.info(
        f"Migration to configuration version {config_entry.version} successful"
    )

    return True


### Temporarily removed to simplify initial core submission review - will be re-added in a future PR
# async def async_register_frontend(hass: HomeAssistant) -> None:
#     """Register frontend modules after HA startup."""
#     module_register = JSModuleRegistration(hass)
#     await module_register.async_register()


# @websocket_api.websocket_command(
#     {
#         vol.Required("type"): f"{DOMAIN}/version",
#     }
# )
# @websocket_api.async_response
# async def websocket_get_version(
#     hass: HomeAssistant,
#     connection: websocket_api.ActiveConnection,
#     msg: dict,
# ) -> None:
#     """Handle version request from frontend."""
#     connection.send_result(
#         msg["id"],
#         {"version": INTEGRATION_VERSION},
#     )


async def async_setup(hass: HomeAssistant, config_entry: TransportNSWConfigEntry):

    ### Temporarily removed to simplify initial core submission review - will be re-added in a future PR
    # # Register websocket command for version checking of the Lovelace card
    # websocket_api.async_register_command(hass, websocket_get_version)

    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: TransportNSWConfigEntry
) -> bool:
    """Set up the ha_transportnsw integration from a config entry."""

    ### Temporarily removed to simplify initial core submission review - will be re-added in a future PR
    # # We need to register the Frontend .JS module, which will be unloaded if the Integration is itself unloaded or reloaded by the user
    # # We have to do this here as async_setup is only ever called at HA startup, never again for an Integration reload
    # # As there could potentially be multiple config entries (unlikely, to be fair) we need to cater for that

    # # Initialize our cross-entry tracking container if missing
    # try:
    #     if DOMAIN not in hass.data or "frontend_loaded" not in hass.data[DOMAIN]:
    #         hass.data[DOMAIN] = {
    #             "frontend_loaded": False  # Stores active entry_id strings
    #         }

    #     # If this is the first entry load we need to register the Javascript module(s)
    #     if not hass.data[DOMAIN]["frontend_loaded"]:
    #         # Register the module specific to this Integration
    #         async def _setup_frontend(_event=None) -> None:
    #             await async_register_frontend(hass)

    #         # If HA is already running, register immediately
    #         if hass.state == CoreState.running:
    #             await _setup_frontend()
    #         else:
    #             # Otherwise, wait for the STARTED event
    #             hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _setup_frontend)

    #         # Finally make a note that the frontend has been loaded, or will be once HA is running, so other entries know not to do it themselves
    #         hass.data[DOMAIN]["frontend_loaded"] = True

    # except Exception as ex:
    #     _LOGGER.error(f"Error registering frontend module: {ex}")

    try:
        # Force a quick check and update of the selected sensors if 'verbose', this catches all future sensors that are created
        for subentry in config_entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_JOURNEY:
                sensor_creation_option = subentry.data.get(CONF_SENSOR_CREATION, "none")
                if sensor_creation_option == "verbose":
                    # Make a copy of the data, update it and then re-save it
                    # This allows us to automatically enable the creation of any new
                    # sensors since the user previously selected 'all sensors' and would
                    # reasonably expect new sensors to appear automatically

                    current_sensor_options = get_optional_sensors(subentry.data.copy())
                    new_sensor_options = set_optional_sensors(sensor_creation_option)

                    if new_sensor_options != current_sensor_options:
                        # Only update if the options are different
                        new_data = subentry.data.copy()
                        new_data.update(new_sensor_options)

                        hass.config_entries.async_update_subentry(
                            config_entry, subentry, data=new_data
                        )
                        _LOGGER.info("Updated sensor options")
                    else:
                        _LOGGER.debug("Sensors options unchanged")

    except Exception as ex:
        _LOGGER.warning(f"Error updating optional sensors: {ex}")

    try:
        # Initialise the persistent api_data storage
        api_store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{config_entry.entry_id}")
        _LOGGER.debug(f"Initialised persistent storage for {config_entry.title}")

    except Exception as ex:
        # This is a fatal error - ideally we'd be able to count API usage.  Without it we can't do automatic polling calculations though
        # TODO: Make this a warning error and disable automatic polling calculations
        _LOGGER.error(f"Error initialising persistent storage: {ex}")
        return False

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
