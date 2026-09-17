"""Helper functions for TransportNSWv2 API"""

import json
import logging

# from pathlib import Path
import os
from datetime import datetime, time

from TransportNSWv2 import (
    APIRateLimitExceeded,
    InvalidAPIKey,
    StopError,
    TransportNSWv2,
    TripError,
)

from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.util import dt as dt_util

from .const import (
    API_DAILY_LIMIT,
    CONF_CHANGES_SENSOR,
    CONF_DELAY_SENSOR,
    CONF_DESTINATION_DETAIL_SENSOR,
    CONF_DESTINATION_DEVICE_TRACKER,
    CONF_DESTINATION_NAME_SENSOR,
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
    CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR,
    CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR,
    CONF_LAST_LEG_ARRIVAL_TIME_SENSOR,
    CONF_LAST_LEG_DEVICE_TRACKER,
    CONF_LAST_LEG_LINE_NAME_SENSOR,
    CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR,
    CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR,
    CONF_LAST_LEG_OCCUPANCY_SENSOR,
    CONF_LAST_LEG_RUN_NAME_SENSOR,
    CONF_LAST_LEG_TRAIN_SET_SENSOR,
    CONF_LAST_LEG_TRANSPORT_NAME_SENSOR,
    CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR,
    CONF_ORIGIN_DETAIL_SENSOR,
    CONF_ORIGIN_DEVICE_TRACKER,
    CONF_ORIGIN_NAME_SENSOR,
    CONF_START_TIME,
    DEFAULT_DESTINATION_DEVICE_TRACKER,
    DEFAULT_END_TIME,
    DEFAULT_FIRST_LEG_DEVICE_TRACKER,
    DEFAULT_LAST_LEG_DEVICE_TRACKER,
    DEFAULT_ORIGIN_DEVICE_TRACKER,
    DEFAULT_START_TIME,
    DOMAIN,
    MIN_AUTO_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def within_poll_time(subentry):
    """Are we within the start/stop times for this subentry?"""
    now = dt_util.now().time()

    start_time = time.fromisoformat(
        subentry.data.get(CONF_START_TIME, DEFAULT_START_TIME)
    )

    end_time = time.fromisoformat(subentry.data.get(CONF_END_TIME, DEFAULT_END_TIME))

    if not start_time <= now <= end_time:
        # We are outside of the poll time - return False, plus when the polling will start
        return False, start_time
    else:
        # We are inside the poll time - return True, plus when the polling will stop unless it's the default
        if end_time == time.fromisoformat(DEFAULT_END_TIME):
            return True, None
        else:
            return True, end_time


def get_auto_poll_interval(
    coordinator, percent_available: int, end_time: str = DEFAULT_END_TIME
) -> int:
    """Return how often we can poll based on the current average API calls
    per poll and how far through the day we are - with 5% headroom."""

    # How many API calls do we have left for the day?
    remaining_api_calls = API_DAILY_LIMIT - coordinator.daily_api_calls

    # How long do we have until midnight, or we stop polling for the day (whichever happens first?
    now = dt_util.now()
    target_time = datetime.strptime(end_time, "%H:%M:%S").time()
    end_time_tz = datetime.combine(
        now.date(),
        target_time,
        tzinfo=now.tzinfo,
    )
    minutes_until_last_window = (end_time_tz - now).total_seconds() / 60

    # How many polls can we do based on the current per-poll API call average?  Factor in the percent of the daily allocation that's available to this Integration
    if coordinator.rolling_average_api_calls > 0:
        max_polls = int(
            (remaining_api_calls / coordinator.rolling_average_api_calls)
            * percent_available
        )
        min_refresh_rate_secs = int((minutes_until_last_window / max_polls) * 60) + 1
    else:
        min_refresh_rate_secs = MIN_AUTO_SCAN_INTERVAL

    return (
        min_refresh_rate_secs
        if min_refresh_rate_secs > MIN_AUTO_SCAN_INTERVAL
        else MIN_AUTO_SCAN_INTERVAL
    )


def get_journey_data(coordinator_data, subentry_id: str, journey_index: int):
    """Check to make sure that there is in fact journey data for this specific journey, otherwise return None."""
    if (
        coordinator_data is not None
        and subentry_id in coordinator_data
        and len(coordinator_data[subentry_id]) >= (journey_index + 1)
    ):
        return coordinator_data[subentry_id][journey_index]

    return None


def extract_from_hierarchy(obj, path, separator=".", default=None) -> str | float:
    """Traverses a nested dict/list hierarchy using a dot-separated path (e.g., 'users.0.name')."""
    if obj is None or path is None:
        return default
    else:
        keys = path.split(separator)
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]

            elif isinstance(obj, list):
                try:
                    obj = obj[int(key)]

                except (ValueError, IndexError):
                    return default
            else:
                return default

        return obj


def get_device_trackers(hass: HomeAssistant, entity_filter: str):
    # Return a list of Mobile App-sourced device tracker entities, or just the details for a single tracker

    device_trackers = []
    entity_reg = er.async_get(hass)

    for entity_id, EntRegItem in entity_reg.entities.items():
        if (
            "device_tracker" in entity_id
            and "mobile_app" in EntRegItem.platform
            and entity_filter in entity_id
        ):
            if EntRegItem.name is None:
                entity_name = EntRegItem.original_name
            else:
                entity_name = EntRegItem.name

            device_trackers.append(
                selector.SelectOptionDict(value=entity_id, label=entity_name)
            )

    return device_trackers


def get_trips(
    api_key: str,
    name_origin: str,
    name_destination: str,
    journey_wait_time: int = 0,
    origin_transport_type: int = [1],
    destination_transport_type: int = [1],
    strict_transport_type: bool = False,
    route_filter: str = "",
    run_filter: str = "",
    journeys_to_return: int = 1,
    include_realtime_location: bool = True,
    include_alerts: bool = False,
    alert_severity: str = "high",
    alert_type: str = ["all"],
    max_changes: int = 5,
):

    # Use the Transport NSW API to request trip information
    # Exceptions will be caught by the calling function

    try:
        if not include_alerts:
            alert_severity = "none"

        sleep_time = 0.5  # This will be important later
        tfnsw = TransportNSWv2()

        data = tfnsw.get_trip(
            api_key=api_key,
            name_origin=name_origin,
            name_destination=name_destination,
            journey_wait_time=journey_wait_time,
            origin_transport_type=origin_transport_type,
            destination_transport_type=destination_transport_type,
            strict_transport_type=strict_transport_type,
            raw_output=False,
            run_filter=run_filter,
            route_filter=route_filter,
            journeys_to_return=journeys_to_return,
            include_realtime_location=include_realtime_location,
            include_alerts=alert_severity,
            alert_type=alert_type,
            check_stop_ids=False,
            max_changes=max_changes,
            sleep_time=sleep_time,
        )

        return json.loads(data)

    except (InvalidAPIKey, APIRateLimitExceeded, StopError, TripError):
        raise

    except Exception as err:
        raise TripError from err


def check_stops(api_key: str, stops: list[str]):
    # Check all provided stops using the Transport NSW API, and return all the associated stop metadata
    # Exceptions will be captured by the calling function

    try:
        tfnsw = TransportNSWv2()
        data = tfnsw.check_stops(api_key=api_key, stops=stops)

        return json.loads(data)

    except InvalidAPIKey as err:
        raise InvalidAPIKey from err

    except APIRateLimitExceeded as err:
        raise APIRateLimitExceeded from err

    except StopError as err:
        raise StopError from err

    except Exception as err:
        raise StopError from err


def get_stop_detail(stop_data, stop_id: str, property: str):
    # Return a specific property from the provided stop metadata
    stop_detail = "n/a"

    for stop in stop_data["stop_list"]:
        if "stop_id" in stop and stop["stop_id"] == stop_id:
            stop_detail = stop["stop_detail"]["disassembledName"]
            break

    return stop_detail


def get_optional_sensors(subentry_data: str):
    # Return the current subentry options in the same format as 'set_optional_sensors' for comparison
    optional_sensors = {}

    for option_group in [
        "time_and_change_sensors",
        "origin_sensors",
        "destination_sensors",
        "device_trackers",
    ]:
        if option_group in subentry_data:
            optional_sensors[option_group] = subentry_data[option_group]

    return optional_sensors


def set_optional_sensors(sensor_creation: str):
    # Determine which optional sensors to create

    # These are for the new integration
    if sensor_creation == "changes_and_times":
        sensor_options = {
            "time_and_change_sensors": {
                CONF_CHANGES_SENSOR: True,
                CONF_DELAY_SENSOR: True,
                CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR: True,
                CONF_LAST_LEG_ARRIVAL_TIME_SENSOR: True,
                CONF_DURATION_SENSOR: True,
            },
            "origin_sensors": {
                CONF_ORIGIN_NAME_SENSOR: False,
                CONF_ORIGIN_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_RUN_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_TRAIN_SET_SENSOR: False,
            },
            "destination_sensors": {
                CONF_DESTINATION_NAME_SENSOR: False,
                CONF_DESTINATION_DETAIL_SENSOR: False,
                CONF_LAST_LEG_RUN_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_LAST_LEG_TRAIN_SET_SENSOR: False,
            },
            "device_trackers": {
                CONF_FIRST_LEG_DEVICE_TRACKER: DEFAULT_FIRST_LEG_DEVICE_TRACKER,
                CONF_LAST_LEG_DEVICE_TRACKER: DEFAULT_FIRST_LEG_DEVICE_TRACKER,
                CONF_ORIGIN_DEVICE_TRACKER: DEFAULT_ORIGIN_DEVICE_TRACKER,
                CONF_DESTINATION_DEVICE_TRACKER: DEFAULT_DESTINATION_DEVICE_TRACKER,
            },
        }

    elif sensor_creation == "verbose":
        sensor_options = {
            "time_and_change_sensors": {
                CONF_CHANGES_SENSOR: True,
                CONF_DELAY_SENSOR: True,
                CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR: True,
                CONF_LAST_LEG_ARRIVAL_TIME_SENSOR: True,
                CONF_DURATION_SENSOR: True,
            },
            "origin_sensors": {
                CONF_ORIGIN_NAME_SENSOR: True,
                CONF_ORIGIN_DETAIL_SENSOR: True,
                CONF_FIRST_LEG_RUN_NAME_SENSOR: True,
                CONF_FIRST_LEG_LINE_NAME_SENSOR: True,
                CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR: True,
                CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR: True,
                CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR: True,
                CONF_FIRST_LEG_OCCUPANCY_SENSOR: True,
                CONF_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR: True,
                CONF_FIRST_LEG_TRAIN_SET_SENSOR: True,
            },
            "destination_sensors": {
                CONF_DESTINATION_NAME_SENSOR: True,
                CONF_DESTINATION_DETAIL_SENSOR: True,
                CONF_LAST_LEG_RUN_NAME_SENSOR: True,
                CONF_LAST_LEG_LINE_NAME_SENSOR: True,
                CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR: True,
                CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR: True,
                CONF_LAST_LEG_TRANSPORT_NAME_SENSOR: True,
                CONF_LAST_LEG_OCCUPANCY_SENSOR: True,
                CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR: True,
                CONF_LAST_LEG_TRAIN_SET_SENSOR: True,
            },
            "device_trackers": {
                CONF_FIRST_LEG_DEVICE_TRACKER: "always",
                CONF_LAST_LEG_DEVICE_TRACKER: "if_not_duplicated",
                CONF_ORIGIN_DEVICE_TRACKER: "always",
                CONF_DESTINATION_DEVICE_TRACKER: "always",
            },
        }

    # These are for migration entries
    elif sensor_creation == "basic":
        sensor_options = {
            "time_and_change_sensors": {
                CONF_CHANGES_SENSOR: True,
                CONF_DELAY_SENSOR: False,
                CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR: False,
                CONF_LAST_LEG_ARRIVAL_TIME_SENSOR: True,
                CONF_DURATION_SENSOR: False,
            },
            "origin_sensors": {
                CONF_ORIGIN_NAME_SENSOR: False,
                CONF_ORIGIN_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_RUN_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_TRAIN_SET_SENSOR: False,
            },
            "destination_sensors": {
                CONF_DESTINATION_NAME_SENSOR: False,
                CONF_DESTINATION_DETAIL_SENSOR: False,
                CONF_LAST_LEG_RUN_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_LAST_LEG_TRAIN_SET_SENSOR: False,
            },
            "device_trackers": {
                CONF_FIRST_LEG_DEVICE_TRACKER: DEFAULT_FIRST_LEG_DEVICE_TRACKER,
                CONF_LAST_LEG_DEVICE_TRACKER: DEFAULT_LAST_LEG_DEVICE_TRACKER,
                CONF_ORIGIN_DEVICE_TRACKER: DEFAULT_ORIGIN_DEVICE_TRACKER,
                CONF_DESTINATION_DEVICE_TRACKER: DEFAULT_DESTINATION_DEVICE_TRACKER,
            },
        }

    elif sensor_creation == "medium":
        sensor_options = {
            "time_and_change_sensors": {
                CONF_CHANGES_SENSOR: True,
                CONF_DELAY_SENSOR: False,
                CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR: False,
                CONF_LAST_LEG_ARRIVAL_TIME_SENSOR: True,
                CONF_DURATION_SENSOR: True,
            },
            "origin_sensors": {
                CONF_ORIGIN_NAME_SENSOR: True,
                CONF_ORIGIN_DETAIL_SENSOR: True,
                CONF_FIRST_LEG_RUN_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_TRAIN_SET_SENSOR: False,
            },
            "destination_sensors": {
                CONF_DESTINATION_NAME_SENSOR: False,
                CONF_DESTINATION_DETAIL_SENSOR: True,
                CONF_LAST_LEG_RUN_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_LAST_LEG_TRAIN_SET_SENSOR: False,
            },
            "device_trackers": {
                CONF_FIRST_LEG_DEVICE_TRACKER: DEFAULT_FIRST_LEG_DEVICE_TRACKER,
                CONF_LAST_LEG_DEVICE_TRACKER: DEFAULT_LAST_LEG_DEVICE_TRACKER,
                CONF_ORIGIN_DEVICE_TRACKER: DEFAULT_ORIGIN_DEVICE_TRACKER,
                CONF_DESTINATION_DEVICE_TRACKER: DEFAULT_DESTINATION_DEVICE_TRACKER,
            },
        }

    else:
        sensor_options = {
            "time_and_change_sensors": {
                CONF_CHANGES_SENSOR: False,
                CONF_DELAY_SENSOR: False,
                CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR: False,
                CONF_LAST_LEG_ARRIVAL_TIME_SENSOR: False,
                CONF_DURATION_SENSOR: False,
            },
            "origin_sensors": {
                CONF_ORIGIN_NAME_SENSOR: False,
                CONF_ORIGIN_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_RUN_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SENSOR: False,
                CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_SENSOR: False,
                CONF_FIRST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_FIRST_LEG_TRAIN_SET_SENSOR: False,
            },
            "destination_sensors": {
                CONF_DESTINATION_NAME_SENSOR: False,
                CONF_DESTINATION_DETAIL_SENSOR: False,
                CONF_LAST_LEG_RUN_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SENSOR: False,
                CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR: False,
                CONF_LAST_LEG_TRANSPORT_NAME_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_SENSOR: False,
                CONF_LAST_LEG_OCCUPANCY_DETAIL_SENSOR: False,
                CONF_LAST_LEG_TRAIN_SET_SENSOR: False,
            },
            "device_trackers": {
                CONF_FIRST_LEG_DEVICE_TRACKER: DEFAULT_FIRST_LEG_DEVICE_TRACKER,
                CONF_LAST_LEG_DEVICE_TRACKER: DEFAULT_LAST_LEG_DEVICE_TRACKER,
                CONF_ORIGIN_DEVICE_TRACKER: DEFAULT_ORIGIN_DEVICE_TRACKER,
                CONF_DESTINATION_DEVICE_TRACKER: DEFAULT_DESTINATION_DEVICE_TRACKER,
            },
        }

    return sensor_options


def delete_legacy_storage(base_path: str, config_entry):
    """Delete the old persistent API storage file.
    We've moved to using the Store helpers instead."""
    file_path = f"{base_path}/custom_components/{DOMAIN}/.{DOMAIN}_{config_entry.data[CONF_API_KEY]}.json"

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

    except PermissionError:
        # Not much we can do about that - just ignore it
        pass


def remove_entity(entity_reg, configentry_id, subentry_id, trip_index, key):
    # Search for and remove a sensor that's no longer needed
    unique_id = f"{subentry_id}_{key}_{trip_index}"

    try:
        # Get all the entities for this config entry
        entities = entity_reg.entities.get_entries_for_config_entry_id(configentry_id)

        # Search for the one to remove
        for entity in entities:
            if entity.unique_id == unique_id:
                entity_reg.async_remove(entity.entity_id)
                break

    finally:
        # Don't log an error as it's possible the entity never existed in the first place
        pass


def rename_entity(entity_reg, configentry_id, subentry_id, trip_index, key, new_name):
    # Search for and rename a device tracker entity
    unique_id = f"{subentry_id}_{key}_{trip_index}"

    try:
        # Get all the entities for this config entry
        entities = entity_reg.entities.get_entries_for_config_entry_id(configentry_id)

        # Search for the one to remove
        for entity in entities:
            if entity.unique_id == unique_id:
                entity_reg.async_remove(entity.entity_id)
                break

    finally:
        # Don't log an error as it's possible the entity never existed in the first place
        pass


def remove_device(
    device_reg, entry_id, subentry_id, origin_id, destination_id, device_identifier
):
    # Search for and remove a device that's no longer needed
    try:
        if hasattr(device_reg, "async_get_device_by_identifier"):
            # This is the current way of accessing devices
            device = device_reg.async_get_device_by_identifier(
                (
                    DOMAIN,
                    f"{subentry_id}_{origin_id}_{destination_id}_{device_identifier}",
                ),
                entry_id,
            )
        else:
            # This is the deprecated way, or for older versions of HA the only way.
            # TODO: Remove this section when HA 2027.8 is released.
            device = device_reg.async_get_device(
                identifiers={
                    (
                        DOMAIN,
                        f"{subentry_id}_{origin_id}_{destination_id}_{device_identifier}",
                    )
                }
            )

        if device is not None:
            device_reg.async_remove_device(
                device_id=device.id,
            )

    finally:
        # If the device can't be deleted for some reason it's unlikely that we'll be able to do anything about that here, unfortunately
        pass
