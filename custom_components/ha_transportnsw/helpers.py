"""Helper functions for TransportNSWv2 API"""

import json
import logging

# from pathlib import Path
import os

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

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
