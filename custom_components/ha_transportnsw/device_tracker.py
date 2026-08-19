"""Support for tracking transport data."""

from __future__ import annotations
from typing import Tuple
from dataclasses import dataclass

import logging

from homeassistant.components.device_tracker import (
    TrackerEntity,
    TrackerEntityDescription
)

from homeassistant.const import CONF_NAME

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry

from . import TransportNSWConfigEntry
from .const import (
    CONF_DESTINATION_ID,
    CONF_DESTINATION_NAME,
    CONF_FIRST_LEG_DEVICE_TRACKER,
    CONF_FIRST_LEG_DEVICE_TRACKER_FRIENDLY,
    CONF_LAST_LEG_DEVICE_TRACKER,
    CONF_LAST_LEG_DEVICE_TRACKER_FRIENDLY,
    CONF_ORIGIN_DEVICE_TRACKER,
    CONF_ORIGIN_DEVICE_TRACKER_FRIENDLY,
    CONF_DESTINATION_DEVICE_TRACKER,
    CONF_DESTINATION_DEVICE_TRACKER_FRIENDLY,
    CONF_ORIGIN_ID,
    CONF_ORIGIN_NAME,
    CONF_ORIGIN_TYPE,
    CONF_TRIPS_TO_CREATE,
    DEVICE_TRACKER_LOOKUPS,
    DOMAIN,
    JOURNEY_ICONS,
    SUBENTRY_TYPE_JOURNEY,
    TFNSW_ATTRIBUTION
)
from .coordinator import TransportNSWCoordinator
from .helpers import remove_entity, extract_from_hierarchy

_LOGGER = logging.getLogger(__name__)

# Extend the default TrackerEntityDescription class
@dataclass(frozen = True, kw_only = True)
class TransportNSWTrackerEntityDescription(TrackerEntityDescription):
    # Custom extension adding a value path for retrieving simple values from the data returned by DataUpdateCoordinator
    # or a callable function for more complex returns
    # Also stores what 'type' of tracker this is - a vehicle or a location
    
    state_path: str | None = None
    attrs_path: str | None = None
    attrs_friendly: str | None = None
    state_fn: Callable[[Any], Any] | None = None

# state_fn functions
def get_coords(location_data, sensor_key: str, location_key: str) -> float:
    """Return the lat or lon value from the returned data."""

    try:
        # Find the key index
        index = next((i for i, item in enumerate(location_data) if item.get("key") == sensor_key), None)
        if index is None:
            return None

        return location_data[index]['coords'][location_key]

    except:
        return None

def is_duplicate(location_data, sensor_key: str) -> bool:
    """Is this device tracker a duplicate?"""

    try:
        # Find the key index
        index = next((i for i, item in enumerate(location_data) if item.get("key") == sensor_key), None)
        if index is None:
            return False

        return location_data[index]['same_as_origin']

    except:
        return False


# Subentry-level sensor definitions
DEVICE_TRACKER_SENSORS: tuple[TransportNSWTrackerEntityDescription, ...] = (
    TransportNSWTrackerEntityDescription(
        key=CONF_FIRST_LEG_DEVICE_TRACKER,
        name=CONF_FIRST_LEG_DEVICE_TRACKER_FRIENDLY,
#        icon='mdi:clock-outline',
#        device_class = SensorDeviceClass.TIMESTAMP,
        state_fn = get_coords,
        state_path = "vehicles",
    ),
    TransportNSWTrackerEntityDescription(
        key=CONF_LAST_LEG_DEVICE_TRACKER,
        name=CONF_LAST_LEG_DEVICE_TRACKER_FRIENDLY,
#        icon='mdi:clock-outline',
#        device_class = SensorDeviceClass.TIMESTAMP,
        state_fn = get_coords,
        state_path = "vehicles",
    ),
    TransportNSWTrackerEntityDescription(
        key=CONF_ORIGIN_DEVICE_TRACKER,
        name=CONF_ORIGIN_DEVICE_TRACKER_FRIENDLY,
#        icon='mdi:clock-outline',
#        device_class = SensorDeviceClass.TIMESTAMP,
        state_fn = get_coords,
        state_path = "locations",
    ),
    TransportNSWTrackerEntityDescription(
        key=CONF_DESTINATION_DEVICE_TRACKER,
        name=CONF_DESTINATION_DEVICE_TRACKER_FRIENDLY,
#        icon='mdi:clock-outline',
#        device_class = SensorDeviceClass.TIMESTAMP,
        state_fn = get_coords,
        state_path = "locations",
    ),
)

def is_tracker_enabled(tracker: str, data, origin_type: str) -> bool:
    # Determine if the device tracker sensor has been enabled in the options
    # There are a few combinations so doing it here is neater for overall code flow
    try:
        if origin_type == 'stop':
            possible_values = ['always', 'if_not_duplicated']
        else:
            possible_values = ['always', 'if_not_duplicated', 'if_device_tracker_journey']

        if data[tracker] in possible_values:
            return True
        else:
            return False

    except:
        return False


def get_location_value(data, key: str, value: str, index: int = -1) -> Tuple[any, bool]:
    try:
        available = False

        if key in [CONF_FIRST_LEG_DEVICE_TRACKER, CONF_LAST_LEG_DEVICE_TRACKER]:
            source = data['locations_list']['vehicles']
        else:
            source = data['locations_list']['locations']

        result = next((item for item in source if item['key'] == key), None)
        if result is not None:
            available = True

            if index == -1:
                return result[value], available
            else:
                return result[value][index], available

        else:
            return None, False

    except:
        return None, False


def get_device_tracker_name(key, subentry_data, journey_data, device_suffix, leg_suffix) -> str:
    # This function reserved for future naming convention changes...

    # Generate the default name
    name = f"{subentry_data[CONF_ORIGIN_NAME]} to {subentry_data[CONF_DESTINATION_NAME]}{device_suffix} {leg_suffix}"

    return name


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: TransportNSWConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:

    # This gets the data update coordinator from the config entry runtime data as specified in __init__.py
    coordinator: TransportNSWCoordinator = config_entry.runtime_data.coordinator

    entity_reg = entity_registry.async_get(hass)

    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_JOURNEY:
            trips_to_create = subentry.data[CONF_TRIPS_TO_CREATE]
            device_trackers = []

            # Create/remove the device trackers
            for trip_index in range (0, 3, 1):   # TODO - save the previous trip count and only delete extra sensors if needed
                if trips_to_create == 1:
                    sensor_suffix = ""
                    name_suffix = ""
                    device_suffix = ""
                    migration_suffix = ""
                    device_identifier = f"trip_{str(trip_index + 1)}"
                else:
                    sensor_suffix = f"trip_{str(trip_index + 1)}"
                    name_suffix = f" ({str(trip_index + 1)})"
                    device_suffix = f" trip {str(trip_index + 1)}"
                    migration_suffix = f"_trip_{str(trip_index + 1)}"
                    device_identifier = f"trip_{str(trip_index + 1)}"

                for sensor in DEVICE_TRACKER_SENSORS:
#                for tracker in [CONF_FIRST_LEG_DEVICE_TRACKER, CONF_LAST_LEG_DEVICE_TRACKER, CONF_ORIGIN_DEVICE_TRACKER, CONF_DESTINATION_DEVICE_TRACKER]:
                    if trip_index >= trips_to_create:
                        # We've finished creating sensors, now delete sensors that may have been created previously but that aren't needed any more
                        remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)
                    else:
                        if is_tracker_enabled(sensor.key, subentry.data['device_trackers'], subentry.data.get(CONF_ORIGIN_TYPE, 'stop')):

                            # new_device_tracker = TrackerEntityDescription(
                            #     key = tracker,
                            #     name = f"{subentry.subentry_id}_{tracker}_{trip_index}"
                            #     )

                            leg_suffix = DEVICE_TRACKER_LOOKUPS.get(sensor.key, '')

#                            device_trackers.append(TransportNSWDeviceTracker(coordinator, sensor, subentry, trip_index, sensor_suffix, name_suffix, device_suffix, migration_suffix, device_identifier))
                            device_trackers.append(TransportNSWDeviceTracker(coordinator, sensor, subentry, trip_index, sensor_suffix, name_suffix, leg_suffix, device_suffix, migration_suffix, device_identifier))
                        else:
                            # Try and remove it - don't worry if it never existed
                            remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)

            async_add_entities(device_trackers, config_subentry_id = subentry.subentry_id, update_before_add = True)


class TransportNSWDeviceTracker(CoordinatorEntity, TrackerEntity):
    """device tracker."""

    def __init__(self, coordinator: TransportNSWCoordinator, description: TransportNSWTrackerEntityDescription, subentry: ConfigSubentry, index: int, sensor_suffix: str, name_suffix: str, leg_suffix: str, device_suffix: str, migration_suffix: str, device_identifier: str) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self.subentry = subentry
        self.journey_index = index
        self.device_suffix = device_suffix
        self.migration_suffix = migration_suffix
        self.device_identifier = device_identifier
        self.sensor_suffix = sensor_suffix
        self.leg_suffix = leg_suffix

        # Cater for migrated entries with a different naming convention
        if CONF_NAME not in subentry.data or subentry.data[CONF_NAME] == '':
            # Use the new naming convention
            self._attr_unique_id = f"{subentry.subentry_id}_{description.key}_{index}"
            self._attr_name = f"{subentry.data[CONF_ORIGIN_NAME]} to {subentry.data[CONF_DESTINATION_NAME]}{device_suffix} {leg_suffix}"
        else:
            self._attr_unique_id = f"{subentry.data[CONF_NAME]}{migration_suffix} {description.name}"
            self._attr_name = f"{subentry.data[CONF_NAME]}{migration_suffix} location"


    @property
    def latitude(self) -> float | None:
        """Return latitude value of the vehicle/location"""
        try:
            journey_data = self.coordinator.data[self.subentry.subentry_id][self.journey_index]['locations_list'][self.entity_description.state_path]
            value = self.entity_description.state_fn(journey_data, self.entity_description.key, 'latitude')

            return value

        except Exception as ex:
            return None

    @property
    def longitude(self) -> float | None:
        """Return latitude value of the vehicle/location"""
        try:
            journey_data = self.coordinator.data[self.subentry.subentry_id][self.journey_index]['locations_list'][self.entity_description.state_path]
            value = self.entity_description.state_fn(journey_data, self.entity_description.key, 'longitude')

            return value

        except Exception as ex:
            return None

    @property
    def available(self) -> bool:
        """ Return if entity is available - basically check to see if there's data where it should be, not based on if we have location data or not
            Also, for CONF_LAST_LEG_DEVICE_TRACKER we should make ourselves unavailable if it's a duplicate of CONF_LAST_LEG_DEVICE_TRACKER
        """
        
        # If this is CONF_LAST_LEG_DEVICE_TRACKER we care about the user display setting for it
        # For some reason I can't yet work out, returning False doesn't make the entity unavailable!  So I'm hiding it until I can work out why.
        if self.entity_description.key == CONF_LAST_LEG_DEVICE_TRACKER:
            hide_if_duplicated = True if self.subentry.data['device_trackers'][CONF_LAST_LEG_DEVICE_TRACKER] == 'if_not_duplicated' else False

        try:
            if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:
                if self.entity_description.key == CONF_LAST_LEG_DEVICE_TRACKER:
                    journey_data = self.coordinator.data[self.subentry.subentry_id][self.journey_index]['locations_list'][self.entity_description.state_path]
                    duplicated_tracker = is_duplicate(journey_data, self.entity_description.key)

                    # We're going to need access to the entity registry to hide or show the device tracker
                    entity_reg = entity_registry.async_get(self.hass)
                    entity_id = entity_reg.async_get_entity_id('device_tracker', DOMAIN, self._attr_unique_id)

                    if duplicated_tracker and hide_if_duplicated:
                        hidden_by = entity_registry.RegistryEntryHider.INTEGRATION
                    else:
                        hidden_by = None

                    # Hide or unhide the tracker
                    entity_reg.async_update_entity(entity_id, hidden_by=hidden_by)

                if duplicated_tracker and hide_if_duplicated:
                    return False
                else:
                    return super().available and True
            else:
                return False

        except:
            return False

    @property
    def icon(self) -> str:

    # Return the appropriate icon based on transport type
        try:
            if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:
                journey_data = self.coordinator.data[self.subentry.subentry_id][self.journey_index]
    
                if journey_data is not None:
                    # Apply the appropriate icons to a subset of the sensors.  All but two are aligned to the transport type
                    if 'origin'in self.entity_description.key or 'first' in self.entity_description.key:
                        transport_type = extract_from_hierarchy(journey_data, 'origin_transport_detail.type')
                    else:
                        transport_type = extract_from_hierarchy(journey_data, 'destination_transport_detail.type')
                    return JOURNEY_ICONS.get(transport_type, 'mdi:train')
    
        except:
            return 'mdi:train'


    @property
    def device_info(self):

        try:
            if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:
                journey_data = self.coordinator.data[self.subentry.subentry_id][self.journey_index]
    
                if journey_data is not None:
                    if self.entity_description.key in [CONF_FIRST_LEG_DEVICE_TRACKER, CONF_LAST_LEG_DEVICE_TRACKER]:
                        # Change the name on the fly, if required.
                        entity_reg = entity_registry.async_get(self.hass)
                        entity_id = entity_reg.async_get_entity_id('device_tracker', DOMAIN, self._attr_unique_id)

                        new_name = get_device_tracker_name (self.entity_description.key, journey_data, self.subentry.data, self.device_suffix, self.leg_suffix)

        except Exception as ex:
            _LOGGER.error(f"error {ex} in device_tracker.py/device_info")

        """Return device info for this sensor."""
        identifiers = {
        "identifiers": {(DOMAIN, f"{self.subentry.subentry_id}_{self.subentry.data[CONF_ORIGIN_ID]}_{self.subentry.data[CONF_DESTINATION_ID]}_{self.device_identifier}")
        },
        "name": f"{self.subentry.data[CONF_ORIGIN_NAME]} to {self.subentry.data[CONF_DESTINATION_NAME]}{self.device_suffix}",
        "manufacturer": "Transport for NSW"
        }

        return identifiers


    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        attrs = {}
        attrs['attribution'] = TFNSW_ATTRIBUTION

        try:
            if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:
                journey_data = self.coordinator.data[self.subentry.subentry_id][self.journey_index]

                attrs["name"], available = get_location_value(journey_data, self.entity_description.key, 'name')
                attrs["stop_id"], available = get_location_value(journey_data, self.entity_description.key, 'id')

        except:
            pass

        return attrs




