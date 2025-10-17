"""Interfaces with the Transport NSW Mk II API sensors."""

import logging
from datetime import datetime, timezone, timedelta
import pytz
import tzlocal
import time

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import (
    CONF_API_KEY,
    CONF_NAME,
    UnitOfTime,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import EntityCategory

from . import MyConfigEntry
from .const import *
from .coordinator import TransportNSWCoordinator

_LOGGER = logging.getLogger(__name__)


DEFAULT_ENTRY_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=API_CALLS,
        name=API_CALLS_NAME,
        native_unit_of_measurement='calls',
        icon='mdi:counter',
        entity_category=EntityCategory.DIAGNOSTIC
    ),
)

DEFAULT_SUBENTRY_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=CONF_DUE_SENSOR,
        name=CONF_DUE_FRIENDLY,
        native_unit_of_measurement=UnitOfTime.MINUTES
    ),
)

# Create sensor definitions
TIME_AND_CHANGE_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR,
        name=CONF_FIRST_LEG_DEPARTURE_TIME_FRIENDLY,
        icon = 'mdi:clock-outline',
        device_class = SensorDeviceClass.TIMESTAMP
    ),
    SensorEntityDescription(
        key=CONF_LAST_LEG_ARRIVAL_TIME_SENSOR,
        name=CONF_LAST_LEG_ARRIVAL_TIME_FRIENDLY,
        icon = 'mdi:clock-outline',
        device_class = SensorDeviceClass.TIMESTAMP
    ),
    SensorEntityDescription(
        key=CONF_DELAY_SENSOR,
        name=CONF_DELAY_FRIENDLY,
        native_unit_of_measurement=UnitOfTime.MINUTES
    ),
    SensorEntityDescription(
        key=CONF_CHANGES_SENSOR,
        name=CONF_CHANGES_FRIENDLY,
        native_unit_of_measurement = 'changes',
        icon = 'mdi:map-marker-path'
    )
)
CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR = 'origin_transport_type'
CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR = 'origin_transport_name'

ORIGIN_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=CONF_ORIGIN_NAME_SENSOR,
        name=CONF_ORIGIN_NAME_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_FIRST_LEG_LINE_NAME_SENSOR,
        name=CONF_FIRST_LEG_LINE_NAME_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR,
        name=CONF_FIRST_LEG_LINE_NAME_SHORT_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR,
        name=CONF_FIRST_LEG_TRANSPORT_TYPE_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR,
        name=CONF_FIRST_LEG_TRANSPORT_NAME_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_FIRST_LEG_OCCUPANCY_SENSOR,
        name=CONF_FIRST_LEG_OCCUPANCY_FRIENDLY,
    )
)

DESTINATION_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=CONF_DESTINATION_NAME_SENSOR,
        name=CONF_DESTINATION_NAME_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_LAST_LEG_LINE_NAME_SENSOR,
        name=CONF_LAST_LEG_LINE_NAME_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR,
        name=CONF_LAST_LEG_LINE_NAME_SHORT_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR,
        name=CONF_LAST_LEG_TRANSPORT_TYPE_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_LAST_LEG_TRANSPORT_NAME_SENSOR,
        name=CONF_LAST_LEG_TRANSPORT_NAME_FRIENDLY,
    ),
    SensorEntityDescription(
        key=CONF_LAST_LEG_OCCUPANCY_SENSOR,
        name=CONF_LAST_LEG_OCCUPANCY_FRIENDLY,
    )
)

ALERT_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=CONF_ALERTS_SENSOR,
        name=CONF_ALERTS_FRIENDLY,
        icon="mdi:alert-outline"
    ),
)


def get_highest_alert(alerts):
    # Search the alerts and return the highest
    highest_alert = -1
    highest_alert_text = 'None'

    try:
        for alert in alerts:
            if ALERT_PRIORITIES.get(alert['priority'],-1) > highest_alert:
                highest_alert = ALERT_PRIORITIES.get(alert['priority'],-1)
                highest_alert_text = alert['priority']
    
    finally:
        return highest_alert_text


def convert_date(utc_string) -> datetime:
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    
    utc_dt = datetime.strptime(utc_string, fmt)
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)
    local_timezone = tzlocal.get_localzone()
    local_dt = utc_dt.astimezone(local_timezone)
    
    return local_dt

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

    except Exception as err:
        # Don't log an error as it's possible the entity never existed in the first place
        pass

def remove_device(device_reg, subentry_id, origin_id, destination_id, device_identifier):
    # Search for and remove a device that's no longer needed
    try:
        device = device_reg.async_get_device(identifiers={(DOMAIN, f"{subentry_id}_{origin_id}_{destination_id}_{device_identifier}")})
        if device is not None:
            device_reg.async_remove_device(device.id)
    finally:
        pass
        
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: TransportNSWCoordinator = config_entry.runtime_data.coordinator

    # Be ready to remove devices and sensors if required
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    # Create the subentry sensors
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_JOURNEY:
            trips_to_create = subentry.data[CONF_TRIPS_TO_CREATE]

            for trip_index in range (0, 3, 1):
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

                sensors = []
                if trip_index >= trips_to_create:
                    # We've finished creating sensors, now we need to start trying to delete sensors and devices
                    # that may have been created previously but that aren't needed any more
                    for sensor_group in [DEFAULT_SUBENTRY_SENSORS, TIME_AND_CHANGE_SENSORS, ORIGIN_SENSORS, DESTINATION_SENSORS, ALERT_SENSORS]:
                        for sensor in sensor_group:
                            remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)

                    remove_device (device_reg, subentry.subentry_id, subentry.data[CONF_ORIGIN_ID], subentry.data[CONF_DESTINATION_ID], device_identifier)
                else:
                    # Define the default sensors for this trip
                    sensors = [
                        TransportNSWSubentrySensor(coordinator, description, subentry, trip_index, sensor_suffix, name_suffix, device_suffix, device_identifier)
                        for description in DEFAULT_SUBENTRY_SENSORS
                    ]
        
                    # Now the optional sensors
                    if 'time_and_change_sensors' in subentry.data:
                        for sensor in TIME_AND_CHANGE_SENSORS:
                            if subentry.data['time_and_change_sensors'].get(sensor.key, False):
                                sensors.append(TransportNSWSubentrySensor(coordinator, sensor, subentry, trip_index, sensor_suffix, name_suffix, device_suffix, device_identifier))
                            else:
                                # Try and remove it - don't worry if it never existed
                                remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)

                    if 'origin_sensors' in subentry.data:
                        for sensor in ORIGIN_SENSORS:
                            if subentry.data['origin_sensors'].get(sensor.key, False):
                                sensors.append(TransportNSWSubentrySensor(coordinator, sensor, subentry, trip_index, sensor_suffix, name_suffix, device_suffix, device_identifier))
                            else:
                                # Try and remove it - don't worry if it never existed
                                remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)

                    if 'destination_sensors' in subentry.data:
                        for sensor in DESTINATION_SENSORS:
                            if subentry.data['destination_sensors'].get(sensor.key, False):
                                sensors.append(TransportNSWSubentrySensor(coordinator, sensor, subentry, trip_index, sensor_suffix, name_suffix, device_suffix, device_identifier))
                            else:
                                # Try and remove it - don't worry if it never existed
                                remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)

                    for sensor in ALERT_SENSORS:
                        if subentry.data.get(sensor.key, False):
                            sensors.append(TransportNSWSubentrySensor(coordinator, sensor, subentry, trip_index, sensor_suffix, name_suffix, device_suffix, device_identifier))
                        else:
                            # Try and remove it - don't worry if it never existed
                            remove_entity (entity_reg, config_entry.entry_id, subentry.subentry_id, trip_index, sensor.key)

                    # Create the subentry sensors, assuming there are any
                    if len(sensors) > 0:
                        async_add_entities(sensors, config_subentry_id = subentry.subentry_id, update_before_add = True)

                
    # Create the top-level config entry sensors
    configentry_sensors = [
        TransportNSWSensor(coordinator, description, config_entry)
        for description in DEFAULT_ENTRY_SENSORS
    ]

    async_add_entities(configentry_sensors, update_before_add = True)


class TransportNSWSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a configentry sensor."""

    def __init__(self, coordinator: TransportNSWCoordinator, description: SensorEntityDescription, config_entry: MyConfigEntry) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)

        """Initialize the sensor."""
        self.entity_description = description
        self.config_entry = config_entry

        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}_0"
        self._attr_name = f"{description.name}"
 
    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | float | str | datetime:
        """Return the state of the entity."""
            
        return self.coordinator.api_calls

class TransportNSWSubentrySensor(CoordinatorEntity, SensorEntity):
    """Implementation of subentry sensor."""

    def __init__(self, coordinator: TransportNSWCoordinator, description: SensorEntityDescription, subentry: ConfigSubentry, index: int, sensor_suffix: str, name_suffix: str, device_suffix: str, device_identifier: str) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)

        """Initialize the sensor."""
        self.entity_description = description
        self.subentry = subentry
        self.journey_index = index
        self.device_suffix = device_suffix
        self.sensor_suffix = sensor_suffix
        self.device_identifier = device_identifier

        self._attr_unique_id = f"{subentry.subentry_id}_{description.key}_{index}"
        self._attr_name = f"{subentry.data[CONF_ORIGIN_NAME]} to {subentry.data[CONF_DESTINATION_NAME]}{device_suffix} {description.name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this sensor."""
        identifiers = {
        "identifiers": {(DOMAIN, f"{self.subentry.subentry_id}_{self.subentry.data[CONF_ORIGIN_ID]}_{self.subentry.data[CONF_DESTINATION_ID]}_{self.device_identifier}")
                       },
        "name": f"{self.subentry.data[CONF_ORIGIN_NAME]} to {self.subentry.data[CONF_DESTINATION_NAME]}{self.device_suffix}",
        "manufacturer": "Transport for NSW"
        }

        return identifiers


    @property
    def native_value(self) -> int | float | str | datetime:
        """Return the state of the entity."""

        if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:

            try:
                if 'time' in self.entity_description.key:
                    return convert_date(self.coordinator.data[self.subentry.subentry_id][self.journey_index][self.entity_description.key])

                elif self.entity_description.key == CONF_ALERTS_SENSOR:
                    # Store the highest alert value as the state - the specific alerts will go into attributes
                    return get_highest_alert(self.coordinator.data[self.subentry.subentry_id][self.journey_index][self.entity_description.key])

                elif self.entity_description.key in [CONF_FIRST_LEG_OCCUPANCY_SENSOR, CONF_LAST_LEG_OCCUPANCY_SENSOR]:
                    return OCCUPANCY_ICONS.get(self.coordinator.data[self.subentry.subentry_id][self.journey_index][self.entity_description.key], ["mdi:account-question", "Unknown"])[1]

                else:
                    return self.coordinator.data[self.subentry.subentry_id][self.journey_index][self.entity_description.key]
            except:
                pass
        else:
            _LOGGER.debug(f"No data for [{self.subentry.subentry_id}][{self.journey_index}][{self.entity_description.key}] in coordinator")
           
    @property
    def icon(self) -> str:
        if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:
            if self.entity_description.key in [CONF_FIRST_LEG_OCCUPANCY_SENSOR, CONF_LAST_LEG_OCCUPANCY_SENSOR]:
                return OCCUPANCY_ICONS.get(self.coordinator.data[self.subentry.subentry_id][self.journey_index][self.entity_description.key], ["mdi:account-question", "Unknown"])[0]
                
            elif self.entity_description.key in [CONF_DUE_SENSOR, CONF_FIRST_LEG_LINE_NAME_SENSOR, CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR, CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR, CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR, CONF_ORIGIN_NAME_SENSOR]:
               return JOURNEY_ICONS.get(self.coordinator.data[self.subentry.subentry_id][self.journey_index][CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR], "mdi:train")

            elif self.entity_description.key in [CONF_LAST_LEG_LINE_NAME_SENSOR, CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR, CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR, CONF_LAST_LEG_TRANSPORT_NAME_SENSOR, CONF_DESTINATION_NAME_SENSOR]:
               return JOURNEY_ICONS.get(self.coordinator.data[self.subentry.subentry_id][self.journey_index][CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR], "mdi:train")

            elif self.entity_description.key in [CONF_DELAY_SENSOR, CONF_ALERTS_SENSOR]:
                return 'mdi:clock-alert-outline'

            elif self.entity_description.key == CONF_CHANGES_SENSOR:
                return 'mdi:map-marker-path'

            elif 'time' in self.entity_description.key:
                return 'mdi:clock-outline'

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        attrs = {}
        
        # Attributes for all sensors
        try:
            attrs['Attribution'] = ATTRIBUTION
            attrs["Origin ID"] = self.subentry.data[CONF_ORIGIN_ID]
            attrs["Destination ID"] = self.subentry.data[CONF_DESTINATION_ID]

            # Key-specific attributes
            if self.coordinator.data is not None and self.subentry.subentry_id in self.coordinator.data:
                if self.entity_description.key == CONF_CHANGES_SENSOR:
                    # A list of changes in this journey
                    attrs['Changes list'] =  "|".join(self.coordinator.data[self.subentry.subentry_id][self.journey_index][CHANGES_LIST])

                if self.entity_description.key in ['alerts']:
                    # Alerts can be long so they need to go into attributes
                    attrs["Alerts"] = self.coordinator.data[self.subentry.subentry_id][self.journey_index][self.entity_description.key]
        finally:
            return attrs
