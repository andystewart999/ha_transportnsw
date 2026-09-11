"""Subentry flow for Transport NSW Mk II integration."""

from __future__ import annotations

import copy
import logging
from datetime import time
from typing import Any

import voluptuous as vol
from TransportNSWv2 import APIRateLimitExceeded, InvalidAPIKey, StopError, TripError

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import section
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    TimeSelector,
    selector,
)

from .const import (
    ALERT_PRIORITIES,
    ALL_TRANSPORT_TYPE_STRING,
    CONF_ALERT_SEVERITY,
    CONF_ALERT_TYPES,
    CONF_ALERTS_SENSOR,
    CONF_CHANGES_SENSOR,
    CONF_CREATE_REVERSE_TRIP,
    CONF_DELAY_SENSOR,
    CONF_DESTINATION_DETAIL_SENSOR,
    CONF_DESTINATION_DEVICE_TRACKER,
    CONF_DESTINATION_ID,
    CONF_DESTINATION_NAME,
    CONF_DESTINATION_NAME_SENSOR,
    CONF_DESTINATION_TRANSPORT_TYPE,
    CONF_DURATION_SENSOR,
    CONF_END_TIME,
    CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR,
    CONF_FIRST_LEG_DEVICE_TRACKER,
    CONF_FIRST_LEG_LINE_NAME_SENSOR,
    CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR,
    CONF_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR,
    CONF_FIRST_LEG_OCCUPANCY_SENSOR,
    CONF_FIRST_LEG_RUN_NAME_SENSOR,
    CONF_FIRST_LEG_TRAIN_SET_SENSOR,
    CONF_INCLUDE_REALTIME_LOCATION,
    CONF_LAST_LEG_ARRIVAL_TIME_SENSOR,
    CONF_LAST_LEG_DEVICE_TRACKER,
    CONF_LAST_LEG_LINE_NAME_SENSOR,
    CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR,
    CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR,
    CONF_LAST_LEG_OCCUPANCY_SENSOR,
    CONF_LAST_LEG_RUN_NAME_SENSOR,
    CONF_LAST_LEG_TRAIN_SET_SENSOR,
    CONF_MAX_CHANGES,
    CONF_ORIGIN_DETAIL_SENSOR,
    CONF_ORIGIN_DEVICE_TRACKER,
    CONF_ORIGIN_ID,
    CONF_ORIGIN_NAME,
    CONF_ORIGIN_NAME_SENSOR,
    CONF_ORIGIN_TRANSPORT_TYPE,
    CONF_ORIGIN_TYPE,
    CONF_ROUTE_FILTER,
    CONF_RUN_FILTER,
    CONF_SENSOR_CREATION,
    CONF_START_TIME,
    CONF_TRIP_WAIT_TIME,
    CONF_TRIPS_TO_CREATE,
    DEFAULT_ALERT_SEVERITY,
    DEFAULT_ALERT_TYPES,
    DEFAULT_ALERTS_SENSOR,
    DEFAULT_CHANGES_SENSOR,
    DEFAULT_CREATE_REVERSE_TRIP,
    DEFAULT_DELAY_SENSOR,
    DEFAULT_DESTINATION_DETAIL_SENSOR,
    DEFAULT_DESTINATION_DEVICE_TRACKER,
    DEFAULT_DESTINATION_NAME_SENSOR,
    DEFAULT_DURATION_SENSOR,
    DEFAULT_END_TIME,
    DEFAULT_FIRST_LEG_DEPARTURE_TIME_SENSOR,
    DEFAULT_FIRST_LEG_DEVICE_TRACKER,
    DEFAULT_FIRST_LEG_LINE_NAME_SENSOR,
    DEFAULT_FIRST_LEG_LINE_NAME_SHORT_SENSOR,
    DEFAULT_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR,
    DEFAULT_FIRST_LEG_OCCUPANCY_SENSOR,
    DEFAULT_FIRST_LEG_RUN_NAME_SENSOR,
    DEFAULT_FIRST_LEG_TRAIN_SET_SENSOR,
    DEFAULT_LAST_LEG_ARRIVAL_TIME_SENSOR,
    DEFAULT_LAST_LEG_DEVICE_TRACKER,
    DEFAULT_LAST_LEG_LINE_NAME_SENSOR,
    DEFAULT_LAST_LEG_LINE_NAME_SHORT_SENSOR,
    DEFAULT_LAST_LEG_OCCUPANCY_DETAIL_SENSOR,
    DEFAULT_LAST_LEG_OCCUPANCY_SENSOR,
    DEFAULT_LAST_LEG_RUN_NAME_SENSOR,
    DEFAULT_LAST_LEG_TRAIN_SET_SENSOR,
    DEFAULT_MAX_CHANGES,
    DEFAULT_ORIGIN_DETAIL_SENSOR,
    DEFAULT_ORIGIN_DEVICE_TRACKER,
    DEFAULT_ORIGIN_NAME_SENSOR,
    DEFAULT_SENSOR_CREATION,
    DEFAULT_START_TIME,
    DEFAULT_TRANSPORT_TYPE,
    DEFAULT_TRIP_WAIT_TIME,
    DEFAULT_TRIPS_TO_CREATE,
    MAX_MAX_CHANGES,
    MAX_TRIP_WAIT_TIME,
    SUBENTRY_TYPE_JOURNEY,
    TFNSW_STOPFINDER,
)
from .helpers import check_stops, get_device_trackers, set_optional_sensors

_LOGGER = logging.getLogger(__name__)

# def convert_transport_types_friendly_to_numeric(transport_type_list: dict[str]) -> dict[str]:
#     # Convert the text-based transport types to their numeric equivalents
#     # If empty, just use 0 'all transport types'
#     if not transport_type_list:
#         return DEFAULT_TRANSPORT_TYPE_NUMERIC

#     temp_list = []
#     for transport_type in transport_type_list:
#         # Find the key that suits this value
#         keys = [key for key, value in TRANSPORT_TYPE.items() if value == transport_type]
#         temp_list.append(keys[0])

#     return temp_list


def create_subentries(self, config_entry, input_data):

    description_placeholders = {}
    description_placeholders["plural"] = ""

    if input_data[CONF_CREATE_REVERSE_TRIP]:
        # There and back again (two subentries)
        description_placeholders["plural"] = "s"

        return_data = copy.deepcopy(input_data)
        return_data[CONF_ORIGIN_ID] = input_data[CONF_DESTINATION_ID][0]
        return_data[CONF_ORIGIN_NAME] = input_data[CONF_DESTINATION_NAME]
        return_data[CONF_ORIGIN_TRANSPORT_TYPE] = input_data[
            CONF_DESTINATION_TRANSPORT_TYPE
        ]
        return_data[CONF_DESTINATION_ID] = [input_data[CONF_ORIGIN_ID]]
        return_data[CONF_DESTINATION_NAME] = input_data[CONF_ORIGIN_NAME]
        return_data[CONF_DESTINATION_TRANSPORT_TYPE] = input_data[
            CONF_ORIGIN_TRANSPORT_TYPE
        ]
        del return_data[CONF_CREATE_REVERSE_TRIP]

        unique_id_destination = "_".join(return_data[CONF_DESTINATION_ID])
        self.hass.config_entries.async_add_subentry(
            config_entry,
            ConfigSubentry(
                data=return_data,
                subentry_type=SUBENTRY_TYPE_JOURNEY,
                title=f"{return_data[CONF_ORIGIN_NAME]} to {return_data[CONF_DESTINATION_NAME]}",
                unique_id=f"{return_data[CONF_ORIGIN_ID]}_{unique_id_destination}",
            ),
        )

    del input_data[CONF_CREATE_REVERSE_TRIP]

    unique_id_destination = "_".join(input_data[CONF_DESTINATION_ID])
    self.hass.config_entries.async_add_subentry(
        config_entry,
        ConfigSubentry(
            data=input_data,
            subentry_type=SUBENTRY_TYPE_JOURNEY,
            title=f"{input_data[CONF_ORIGIN_NAME]} to {input_data[CONF_DESTINATION_NAME]}",
            unique_id=f"{input_data[CONF_ORIGIN_ID]}_{unique_id_destination}",
        ),
    )

    description_placeholders["title"] = "title placeholder"
    return description_placeholders


class JourneySubEntryFlowHandler(ConfigSubentryFlow):
    """Handle a subentry flow for Transport NSW MK II"""

    async def _validate_input(
        self, hass: HomeAssistant, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Check that the provided stops are valid.  We'll also use this call to get the stop names
        This tests the API key as well.  Exceptions will be caught upstream"""

        errors: dict[str, str] = {}
        config_entry = self._get_entry()

        # Is the origin a device tracker?  If so we don't need to check that it's a valid stop
        if CONF_ORIGIN_TYPE in data and data[CONF_ORIGIN_TYPE] == "device_tracker":
            # Do a quick 'fail-fast' check
            if data[CONF_CREATE_REVERSE_TRIP]:
                # We can't create the reverse trip with a device tracker as the origin
                errors["base"] = "return_journey_device_tracker_error"
                return "", errors

            entity_info = get_device_trackers(hass, data[CONF_ORIGIN_ID])
            stop_list = data[CONF_DESTINATION_ID].copy()

        # CONF_DESTINATION_ID is always going to be a list, but if there's
        # more than one then we can't create a reverse trip also
        else:
            if data[CONF_CREATE_REVERSE_TRIP] and len(data[CONF_DESTINATION_ID]) > 1:
                # We can't create the reverse trip
                errors["base"] = "return_journey_multiple_destination_error"
                return "", errors

            stop_list = data[CONF_DESTINATION_ID].copy()
            stop_list.insert(0, data[CONF_ORIGIN_ID])

        try:
            stop_data = await hass.async_add_executor_job(
                check_stops, config_entry.data[CONF_API_KEY], stop_list
            )

            if stop_data.get("all_stops_valid"):
                # Get the origin and destination stop names, we'll need them to name the subentry

                if data[CONF_ORIGIN_TYPE] == "device_tracker":
                    data[CONF_ORIGIN_NAME] = entity_info[0]["label"]
                    data[CONF_DESTINATION_NAME] = stop_data["stop_list"][0][
                        "stop_detail"
                    ]["disassembledName"]
                    data[CONF_DESTINATION_ID] = stop_data["stop_list"][0]["stop_id"]
                else:
                    data[CONF_ORIGIN_NAME] = stop_data["stop_list"][0]["stop_detail"][
                        "disassembledName"
                    ]
                    data[CONF_ORIGIN_ID] = stop_data["stop_list"][0]["stop_id"]

                    # Strip out the destination ID(s)
                    destination_stops = stop_data["stop_list"][1:]
                    if len(destination_stops) == 1:
                        data[CONF_DESTINATION_NAME] = destination_stops[0][
                            "stop_detail"
                        ]["disassembledName"]
                        data[CONF_DESTINATION_ID] = [destination_stops[0]["stop_id"]]
                    else:
                        # Multiple destinations were provided, so create an appropriate destination name and list of IDs
                        data[CONF_DESTINATION_NAME] = ""
                        data[CONF_DESTINATION_ID] = []

                        for index, _value in enumerate(destination_stops):
                            data[CONF_DESTINATION_ID].append(
                                destination_stops[index]["stop_id"]
                            )
                            if index == 0:
                                separator = ""
                            elif (index + 1) == len(destination_stops):
                                separator = " or "
                            else:
                                separator = ", "

                            data[CONF_DESTINATION_NAME] += (
                                f"{separator}{destination_stops[index]['stop_detail']['disassembledName']}"
                            )

                return {
                    "title": f"{data[CONF_ORIGIN_NAME]} to {data[CONF_DESTINATION_NAME]}"
                }, errors

            else:
                # Find out which stops were bad
                if (
                    not stop_data["stop_list"][0]["valid"]
                    and not stop_data["stop_list"][1]["valid"]
                ):
                    raise StopError("Both stops are invalid", "stoperror_both")

                elif (
                    not stop_data["stop_list"][0]["valid"]
                    and stop_data["stop_list"][1]["valid"]
                ):
                    raise StopError("The origin stop ID is invalid", "stoperror_origin")

                else:
                    raise StopError(
                        "The destination stop ID is invalid", "stoperror_destination"
                    )

                # Unecessary catch-all!
                raise StopError

        except InvalidAPIKey as err:
            raise InvalidAPIKey from err

        except APIRateLimitExceeded as err:
            raise APIRateLimitExceeded from err

        except StopError as err:
            raise StopError(err, err.stop_detail) from err

        except Exception as err:
            raise StopError("Unknown error checking stop IDs", "stoperror") from err

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle the initial step."""

        # Called when you initiate adding an integration via the UI
        errors: dict[str, str] = {}

        if user_input is not None:
            if "device_tracker." in user_input[CONF_ORIGIN_ID]:
                origin_type = "device_tracker"
            else:
                origin_type = "stop"

            user_input.update({CONF_ORIGIN_TYPE: origin_type})

            # The form has been filled in and submitted, so process the data provided.
            try:
                # Validate that the setup data is valid and if not handle errors.
                info, errors = await self._validate_input(self.hass, user_input)

            except InvalidAPIKey:
                errors["base"] = "invalidapikey"

            except APIRateLimitExceeded:
                errors["base"] = "apiratelimitexceeded"

            except StopError as err:
                errors["base"] = err.stop_detail

            except TripError:
                errors["base"] = "triperror"

            except Exception:
                errors["base"] = "unknown"

            # Check for errors
            if "base" not in errors:
                # Validation was successful, so create a unique id for this instance
                # and create the config subentry.

                # Check the unique ID against the existing subentries
                # The actual unique ID will be set during subentry creation later

                # It's possible that the stop validation function
                # returned better stop IDs, so use them
                unique_id_destination = "_".join(user_input[CONF_DESTINATION_ID])
                unique_id = f"{user_input[CONF_ORIGIN_ID]}_{unique_id_destination}"

                if self.source != SOURCE_RECONFIGURE:
                    for existing_subentry in self._get_entry().subentries.values():
                        if existing_subentry.unique_id == unique_id:
                            errors["base"] = "outbound_already_configured"

                    if user_input[CONF_CREATE_REVERSE_TRIP]:
                        unique_id_destination = "_".join(
                            user_input[CONF_DESTINATION_ID]
                        )
                        unique_id = (
                            f"{unique_id_destination}_{user_input[CONF_ORIGIN_ID]}"
                        )

                        for existing_subentry in self._get_entry().subentries.values():
                            if existing_subentry.unique_id == unique_id:
                                errors["base"] = "return_already_configured"

            # Check for errors again - duplicate journeys are an error that
            #  might have just been discovered
            if "base" not in errors:
                # Validation was successful, create the config subentry/subentries

                # Add an empty CONF_NAME field - it's only used for migrated journeys,
                # journeys created via config flow way will use the new naming convention
                user_input.update({CONF_NAME: ""})

                self._input_data = user_input
                placeholders = {"journey_name": info["title"]}
                self.context["title_placeholders"] = placeholders

                # Call the next step
                return await self.async_step_settings()

        # Are we reconfiguring or are we creating a new journey?
        if user_input is None:
            if self.source == SOURCE_RECONFIGURE:
                config_subentry = self._get_reconfigure_subentry()
                user_input = dict(config_subentry.data)

                # Capture the subentry title in case the user has renamed it
                user_input.update({"user_title": config_subentry.title})

                JOURNEY_DATA_SCHEMA = vol.Schema(
                    {
                        vol.Required(
                            CONF_ORIGIN_ID, default=user_input.get(CONF_ORIGIN_ID, "")
                        ): str,
                        vol.Required(
                            CONF_DESTINATION_ID,
                            default=user_input.get(CONF_DESTINATION_ID, ""),
                        ): str,
                    }
                )

            else:
                # We need to create an empty user_input as the upcoming schema
                # definition requires it.  Otherwise we'd have three distinct schema
                # definition creation sections which seems... inelegent?
                user_input = {}

        options = get_device_trackers(self.hass, "")

        JOURNEY_DATA_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_ORIGIN_ID,
                    default=user_input.get(CONF_ORIGIN_ID, ""),
                ): selector(
                    {
                        "select": {
                            "options": options,
                            "mode": "dropdown",
                            "custom_value": True,
                        }
                    }
                ),
                vol.Required(
                    CONF_DESTINATION_ID,
                    default=user_input.get(CONF_DESTINATION_ID, ""),
                ): selector(
                    {
                        "select": {
                            "mode": "dropdown",
                            "custom_value": True,
                            "multiple": True,
                            "options": [],
                        }
                    }
                ),
                vol.Required(
                    CONF_CREATE_REVERSE_TRIP,
                    default=user_input.get(
                        CONF_CREATE_REVERSE_TRIP, DEFAULT_CREATE_REVERSE_TRIP
                    ),
                ): bool,
            }
        )

        description_placeholders = {"tfnsw_stopfinder": TFNSW_STOPFINDER}

        # Show initial form.
        return self.async_show_form(
            step_id="user",
            data_schema=JOURNEY_DATA_SCHEMA,
            description_placeholders=description_placeholders,
            errors=errors,
            last_step=False,
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:

        errors: dict[str, str] = {}
        if user_input is not None:
            # Fix up an issue with how Voluptuous treats empty string fields
            if CONF_RUN_FILTER not in user_input:
                user_input[CONF_RUN_FILTER] = ""
            if CONF_ROUTE_FILTER not in user_input:
                user_input[CONF_ROUTE_FILTER] = ""

            self._input_data.update(user_input)

            return await self.async_step_sensors()

        # Are we reconfiguring or are we creating a new journey?
        if user_input is None:
            if self.source == SOURCE_RECONFIGURE:
                config_subentry = self._get_reconfigure_subentry()
                user_input = dict(config_subentry.data)

                # Capture the subentry title in case the user has renamed it
                user_input.update({"user_title": config_subentry.title})

                self._input_data = user_input

            else:
                # Create the initial defaults
                user_input = {
                    CONF_ORIGIN_TRANSPORT_TYPE: DEFAULT_TRANSPORT_TYPE,
                    CONF_DESTINATION_TRANSPORT_TYPE: DEFAULT_TRANSPORT_TYPE,
                    CONF_MAX_CHANGES: DEFAULT_MAX_CHANGES,
                    CONF_TRIP_WAIT_TIME: DEFAULT_TRIP_WAIT_TIME,
                }

            if (
                CONF_ORIGIN_TYPE in self._input_data
                and self._input_data[CONF_ORIGIN_TYPE] == "device_tracker"
            ):
                description_placeholders = {
                    "journey_name": f"{self._input_data[CONF_ORIGIN_NAME]} to {self._input_data[CONF_DESTINATION_NAME]}",
                    "journey_description": "As this journey starts with your location the assumption is that the first leg will be a walk - so any transport type filters will apply from the second leg.",
                }
            else:
                description_placeholders = {
                    "journey_name": f"{self._input_data[CONF_ORIGIN_NAME]} to {self._input_data[CONF_DESTINATION_NAME]}",
                    "journey_description": "Only journeys with origin and destination legs that start and end with your selected transport types will be considered valid, so if you don't mind a little bit of a walk at either end (getting off at Gadigal Station and walking to Town Hall Station for example), make sure you select 'Walk' as an option.",
                }

            # Create the origin/destination transport selectors - could be inline below,
            # but it would get complicated to see what's happening
            origin_transport_selector = SelectSelector(
                SelectSelectorConfig(
                    options=ALL_TRANSPORT_TYPE_STRING,
                    multiple=True,  # This activates the multi-select behavior
                    mode=SelectSelectorMode.DROPDOWN,  # Forces dropdown mode
                    translation_key="transport_type_selector",
                )
            )

            destination_transport_selector = SelectSelector(
                SelectSelectorConfig(
                    options=ALL_TRANSPORT_TYPE_STRING,
                    multiple=True,  # This activates the multi-select behavior
                    mode=SelectSelectorMode.DROPDOWN,  # Forces dropdown mode
                    translation_key="transport_type_selector",
                )
            )

            optional_text_selector = TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            )

            STEP_SETTINGS_DATA_SCHEMA = vol.Schema(
                {
                    vol.Required(CONF_ORIGIN_TRANSPORT_TYPE): origin_transport_selector,
                    vol.Required(
                        CONF_DESTINATION_TRANSPORT_TYPE
                    ): destination_transport_selector,
                    vol.Optional(CONF_ROUTE_FILTER): optional_text_selector,
                    vol.Optional(CONF_RUN_FILTER): optional_text_selector,
                    vol.Required(CONF_MAX_CHANGES): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=MAX_MAX_CHANGES)
                    ),
                    vol.Required(CONF_TRIP_WAIT_TIME): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=MAX_TRIP_WAIT_TIME)
                    ),
                }
            )

            return self.async_show_form(
                step_id="settings",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_SETTINGS_DATA_SCHEMA, user_input
                ),
                errors=errors,
                last_step=False,
                description_placeholders=description_placeholders,
            )

    async def async_step_sensors(self, user_input=None):
        # Handle sensor options

        """Handle options flow."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._input_data.update(user_input)

            if self._input_data[CONF_SENSOR_CREATION] != "custom":
                user_input[CONF_INCLUDE_REALTIME_LOCATION] = True
                self._input_data.update(user_input)

                sensor_options = set_optional_sensors(
                    self._input_data[CONF_SENSOR_CREATION]
                )

                # Add to the options
                self._input_data.update(sensor_options)

            # Check for errors
            start_time = time.fromisoformat(user_input[CONF_START_TIME])
            end_time = time.fromisoformat(user_input[CONF_END_TIME])
            if start_time >= end_time:
                errors["base"] = "end_time_before_start_time"

            if "base" not in errors:
                # We may need to go to the alerts selection page, the custom sensors selection page, or both
                if self._input_data[CONF_ALERTS_SENSOR]:
                    # Show the alerts form - it will then show the custom sensors form if required
                    return await self.async_step_alerts()
                else:
                    self._input_data.update(
                        {CONF_ALERT_SEVERITY: "none", CONF_ALERT_TYPES: []}
                    )

                # No more flows to process so we can create/update the subentries as required
                if self.source == SOURCE_RECONFIGURE:
                    # We don't need to recreate the subentry, just refresh and reload the one we're reconfiguring
                    unique_id_destination = "_".join(
                        self._input_data[CONF_DESTINATION_ID]
                    )

                    # Continue to use the existing title, in case the user has renamed it
                    return self.async_update_reload_and_abort(
                        self._get_entry(),
                        self._get_reconfigure_subentry(),
                        unique_id=f"{self._input_data[CONF_ORIGIN_ID]}_{unique_id_destination}",
                        data=self._input_data,
                        title=self._input_data["user_title"],
                    )

                else:
                    description_placeholders = create_subentries(
                        self, self._get_entry(), self._input_data
                    )

                    # We don't have an update listener in place, it causes issues if adding multiple subentries in one go, so we force an update here
                    await self.hass.config_entries.async_reload(
                        self._get_entry().entry_id
                    )

                    return self.async_abort(
                        reason="subentries_created",
                        description_placeholders=description_placeholders,
                    )

        # We get here if there was no user input
        if self.source == SOURCE_RECONFIGURE:
            config_subentry = self._get_reconfigure_subentry()
            user_input = dict(config_subentry.data)

            # Capture the subentry title in case the user has renamed it
            user_input.update({"user_title": config_subentry.title})
        else:
            user_input = {}

        STEP_SENSORS_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_ALERTS_SENSOR,
                    default=user_input.get(CONF_ALERTS_SENSOR, DEFAULT_ALERTS_SENSOR),
                ): bool,
                vol.Required(
                    CONF_TRIPS_TO_CREATE,
                    default=user_input.get(
                        CONF_TRIPS_TO_CREATE, DEFAULT_TRIPS_TO_CREATE
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=3)),
                vol.Required(
                    CONF_START_TIME,
                    default=user_input.get(CONF_START_TIME, DEFAULT_START_TIME),
                ): TimeSelector(),
                vol.Required(
                    CONF_END_TIME,
                    default=user_input.get(CONF_END_TIME, DEFAULT_END_TIME),
                ): TimeSelector(),
            }
        )

        multi_destination_suggestion = (
            (
                "\n\nAs this journey has multiple potential destinations you may want "
                "to include one of the 'destination name' sensors, otherwise it won't "
                "be obvious which destination each journey is using"
            )
            if len(self._input_data[CONF_DESTINATION_ID]) > 1
            else ""
        )

        return self.async_show_form(
            step_id="sensors",
            data_schema=STEP_SENSORS_SCHEMA,
            errors=errors,
            last_step=False,
            description_placeholders={
                "journey_name": f"{self._input_data[CONF_ORIGIN_NAME]} to {self._input_data[CONF_DESTINATION_NAME]}",
                "multi_destination_suggestion": multi_destination_suggestion,
            },
        )

    async def async_step_alerts(self, user_input=None):
        # Handle alerts if requested

        errors: dict[str, str] = {}

        if user_input is not None:
            self._input_data.update(user_input)

            # No more flows to process so we can create/update
            # the subentries as required
            if self.source == SOURCE_RECONFIGURE:
                unique_id_destination = "_".join(
                    self._input_data[CONF_DESTINATION_ID]
                )

                # Continue to use the existing title, in case the
                # user has renamed it
                return self.async_update_reload_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    unique_id=f"{self._input_data[CONF_ORIGIN_ID]}_{unique_id_destination}",
                    data=self._input_data,
                )
            else:
                description_placeholders = create_subentries(
                    self, self._get_entry(), self._input_data
                )
                await self.hass.config_entries.async_reload(
                    self._get_entry().entry_id
                )

                return self.async_abort(
                    reason="subentries_created",
                    description_placeholders=description_placeholders,
                )

        # We get here if there was no user input
        if self.source == SOURCE_RECONFIGURE:
            config_subentry = self._get_reconfigure_subentry()
            user_input = dict(config_subentry.data)

            # Capture the subentry title in case the user has renamed it
            user_input.update({"user_title": config_subentry.title})
        else:
            user_input = {}

        alerts_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ALERT_SEVERITY,
                    default=user_input.get(
                        CONF_ALERT_SEVERITY, DEFAULT_ALERT_SEVERITY
                    ),
                ): selector(
                    {
                        "select": {
                            "options": list(ALERT_PRIORITIES),
                            "mode": "dropdown",
                            "multiple": False,
                            "translation_key": "alert_priority_selector",
                        }
                    }
                ),
                vol.Required(
                    CONF_ALERT_TYPES,
                    default=user_input.get(CONF_ALERT_TYPES, DEFAULT_ALERT_TYPES),
                ): selector(
                    {
                        "select": {
                            "options": DEFAULT_ALERT_TYPES,
                            "mode": "list",
                            "multiple": True,
                            "translation_key": "alert_type_selector",
                        }
                    }
                ),
            }
        )

        if self._input_data[CONF_SENSOR_CREATION] == "custom":
            last_step = False
        else:
            last_step = True

        return self.async_show_form(
            step_id="alerts",
            data_schema=alerts_schema,
            errors=errors,
            last_step=last_step,
            description_placeholders={
                "journey_name": f"{self._input_data[CONF_ORIGIN_NAME]} to {self._input_data[CONF_DESTINATION_NAME]}"
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """User flow to modify an existing location.
           I've left reconfigure in for this initial submission as for subentries
           it's effectively their version of OptionsFlow, which IS permitted in the PR guidelines."""

        return await self.async_step_settings()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
