"""Support for tracking transport data."""

from __future__ import annotations
import logging

from homeassistant.components.device_tracker import (
    TrackerEntity,
    TrackerEntityDescription
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers import entity_registry

from . import MyConfigEntry
from .const import *
from .coordinator import ExampleCoordinator

_LOGGER = logging.getLogger(__name__)

def remove_entity(entity_reg, configentry_id, subentry_id,trip_index, key):
    # Search for and remove a sensor that's no longer needed
    unique_id = f"{subentry_id}_{key}_{trip_index}"

    try:
        # Get all the entities for this config entry
        entities = entity_reg.entities.get_entries_for_config_entry_id(configentry_id)

        # Search for the one to remove
        # TODO - probably we can do this in a one-liner!
        for entity in entities:
            if entity.unique_id == unique_id:
                entity_reg.async_remove(entity.entity_id)
                break

    except Exception as err:
        # Don't log an error as it's possible the entity never existed in the first place
        pass


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Configure device_trackers from a config entry created in the integrations UI."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: ExampleCoordinator = config_entry.runtime_data.coordinator

    # Be ready to remove sensors if required
    entity_reg = entity_registry.async_get(hass)

    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_JOURNEY:
            trips_to_create = subentry.data[CONF_TRIPS_TO_CREATE]
            device_trackers = []

            for trip_index in range (0, 3, 1):   # TODO - consider doing 0 to 4, and if greater than trips_to_create then just delete?
            #for trip_index in range (0, trips_to_create, 1):
                if trips_to_create == 1:
                    sensor_suffix = ""
                    name_suffix = ""
                    device_suffix = ""
                    device_identifier = f"trip_{str(trip_index + 1)}"
                else:
                    sensor_suffix = f"trip_{str(trip_index + 1)}"
                    name_suffix = f" ({str(trip_index + 1)})"
                    device_suffix = f" trip {str(trip_index + 1)}"
                    device_identifier = f"trip_{str(trip_index + 1)}"

                leg_suffix = ""
                for tracker in [CONF_FIRST_LEG_DEVICE_TRACKER, CONF_LAST_LEG_DEVICE_TRACKER]:
                    if trip_index >= trips_to_create:
                    # We've finished creating sensors, now we need to start trying to delete sensors and devices
                    # that may have been created previously but that aren't needed any more
                        remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, tracker)
                    else:
                        if tracker == CONF_FIRST_LEG_DEVICE_TRACKER:
                            tracker_enabled = subentry.data['origin_sensors'][CONF_FIRST_LEG_DEVICE_TRACKER]
                            leg_suffix = "first leg "
                        else:
                            tracker_enabled = (subentry.data['destination_sensors'][CONF_LAST_LEG_DEVICE_TRACKER] != 'never')
                            leg_suffix = "last leg "

                        if tracker_enabled:
                            new_device_tracker = TrackerEntityDescription(
                                key = tracker,
                                name = f"{subentry.subentry_id}_{tracker}_{trip_index}"
                                )

                            device_trackers.append(ExampleDeviceTracker(coordinator, new_device_tracker, subentry, trip_index, sensor_suffix, name_suffix, leg_suffix, device_suffix, device_identifier))
                        else:
                            # Try and remove it - don't worry if it never existed
                            remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, tracker)

            async_add_entities(device_trackers, config_subentry_id = subentry.subentry_id)


class ExampleDeviceTracker(CoordinatorEntity, TrackerEntity):
    """device tracker."""

    def __init__(self, coordinator: ExampleCoordinator, description: TrackerEntityDescription, subentry: ConfigSubentry, index: int, sensor_suffix: str, name_suffix: str, leg_suffix: str, device_suffix: str, device_identifier: str) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)

        """Initialize the sensor."""
        self.entity_description = description
        self.subentry = subentry
        self.journey_index = index
        self.device_suffix = device_suffix
        self.device_identifier = device_identifier
        self.sensor_suffix = sensor_suffix
        self.leg_suffix = leg_suffix

        #self.entity_id = f"device_tracker.{config_entry.entry_id}_{index}_{journey_part}"
        self._attr_unique_id = f"{subentry.subentry_id}_{description.key}_{index}"
        self._attr_name = f"{subentry.data[CONF_ORIGIN_NAME]} to {subentry.data[CONF_DESTINATION_NAME]}{device_suffix} {leg_suffix}location"


    @property
    def latitude(self) -> float | None:
        """Return latitude value of the vehicle."""
        try:
            return self.coordinator.data[self.subentry.subentry_id][self.journey_index][ORIGIN_LATITUDE]

        except:
            pass

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the vehicle."""
        try:
            return self.coordinator.data[self.subentry.subentry_id][self.journey_index][ORIGIN_LONGITUDE]

        except:
            pass

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        try:
            # Make sure there is GPS data
            if self.coordinator.data[self.subentry.subentry_id][self.journey_index][ORIGIN_LATITUDE] != 'n/a' and self.coordinator.data[self.subentry.subentry_id][self.journey_index][ORIGIN_LONGITUDE] != 'n/a':
                # If this is the last leg sensor, and it's the same realtime trip ID as the first leg sensor, should we make it unavailable?
                if self.entity_description.key != CONF_LAST_LEG_DEVICE_TRACKER:
                    return True
                else:
                    # It's the last leg sensor, so check
                    if self.coordinator.data[self.subentry.subentry_id][self.journey_index]['origin_real_time_trip_id'] == self.coordinator.data[self.subentry.subentry_id][self.journey_index]['destination_real_time_trip_id']:
                        return False
                    else:
                        return True
            else:            
                return False
                
        except:
            return False

    @property
    def icon(self) -> str:
        try:
            if self.entity_description.key == CONF_FIRST_LEG_DEVICE_TRACKER:
                return JOURNEY_ICONS.get(self.coordinator.data[self.subentry.subentry_id][self.journey_index][CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR], "mdi:train")
            else:
                return JOURNEY_ICONS.get(self.coordinator.data[self.subentry.subentry_id][self.journey_index][CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR], "mdi:train")

        except:
            return "mdi:train"

    @property
    def device_info(self):
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
        # Add any additional attributes you want on your sensor.
        attrs = {}
        attrs["Origin ID"] = self.subentry.data[CONF_ORIGIN_ID]
        attrs["Destination ID"] = self.subentry.data[CONF_DESTINATION_ID]
        attrs["Subentry ID"] = str(self.subentry.subentry_id)

        if self.entity_description.key == CONF_FIRST_LEG_DEVICE_TRACKER:
            attrs["Realtime trip ID"] = self.coordinator.data[self.subentry.subentry_id][self.journey_index]['origin_real_time_trip_id']
        else:
            attrs["Realtime trip ID"] = self.coordinator.data[self.subentry.subentry_id][self.journey_index]['destination_real_time_trip_id']

        return attrs
