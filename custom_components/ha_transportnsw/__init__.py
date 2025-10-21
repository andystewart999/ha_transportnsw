"""The Transport NSW Mk II integration."""

from __future__ import annotations

from collections import defaultdict
#from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigSubentryData #, ConfigSubentry 
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import Platform, CONF_API_KEY, CONF_SCAN_INTERVAL

from .helpers import check_stops, set_optional_sensors
from .coordinator import TransportNSWCoordinator
from .const import (
    DOMAIN, 
    CONF_ORIGIN_ID,
    CONF_DESTINATION_ID,
    CONF_ORIGIN_NAME,
    CONF_DESTINATION_NAME,
    CONF_ORIGIN_TRANSPORT_TYPE,
    CONF_DESTINATION_TRANSPORT_TYPE,
    CONF_TRIP_WAIT_TIME,
    CONF_TRIPS_TO_CREATE,
    CONF_INCLUDE_REALTIME_LOCATION,
    CONF_FIRST_LEG_DEVICE_TRACKER,
    CONF_LAST_LEG_DEVICE_TRACKER,
    CONF_ALERTS_SENSOR,
    CONF_ALERT_SEVERITY,
    CONF_ALERT_TYPES,
    CONF_RETURN_INFO,
    CONF_ROUTE_FILTER,
    DEFAULT_SCAN_INTERVAL,
    SUBENTRY_TYPE_JOURNEY
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.DEVICE_TRACKER]

type MyConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: DataUpdateCoordinator

async def get_migration_data(hass, yaml_entry):
     # Convert a migrated YAML entry into ConfigSubentryData data and return it along with the api key

    try:
        api_key = yaml_entry[CONF_API_KEY]
        scan_interval = DEFAULT_SCAN_INTERVAL

        origin_id = str(yaml_entry[CONF_ORIGIN_ID])
        destination_id = str(yaml_entry[CONF_DESTINATION_ID])
        transport_type = yaml_entry.get('transport_type', 0)
        trip_wait_time = yaml_entry.get(CONF_TRIP_WAIT_TIME, 0)
        return_info  = yaml_entry[CONF_RETURN_INFO]
        trips_to_create = yaml_entry.get(CONF_TRIPS_TO_CREATE, 1)
        route_filter = yaml_entry.get(CONF_ROUTE_FILTER, '')
        include_realtime_location = yaml_entry.get(CONF_INCLUDE_REALTIME_LOCATION, True)
        alert_severity = yaml_entry.get(CONF_ALERT_SEVERITY, 'none')
        alert_types = yaml_entry.get(CONF_ALERT_TYPES, ["lineinfo", "routeinfo", "stopinfo", "stopblocking", "bannerinfo"])
        
        # Transport type needs to be a list, and we'll assume the destination transport type should be the same as that's the current behaviour
        origin_transport_type = [transport_type]
        destination_transport_type= [transport_type]

        # Get the full list of sensors based on the imported 'return_info'
        sensor_options = set_optional_sensors(return_info)
        
        # Alerts
        if alert_severity != 'none':
            include_alerts = True
        else:
            include_alerts = False
            
        # Real-time location
        if include_realtime_location:
            sensor_options['origin_sensors'][CONF_FIRST_LEG_DEVICE_TRACKER] = True
            sensor_options['destination_sensors'][CONF_LAST_LEG_DEVICE_TRACKER] = 'always'
        else:
            sensor_options['origin_sensors'][CONF_FIRST_LEG_DEVICE_TRACKER] = False
            sensor_options['destination_sensors'][CONF_LAST_LEG_DEVICE_TRACKER] = 'never'

        # We need the stop names for the title, so get them now
        #stop_data = check_stops(api_key, [origin_id, destination_id])
        stop_data = await hass.async_add_executor_job (
             check_stops,
             api_key,
             [origin_id, destination_id]
             )
        
        if stop_data['all_stops_valid']:
            # Get the origin and destination stop names
            origin_name = stop_data['stop_list'][0]['stop_detail']['disassembledName']
            destination_name = stop_data['stop_list'][1]['stop_detail']['disassembledName']

        # Now put it all together
        subentry_data = {
            CONF_ORIGIN_ID: origin_id,
            CONF_ORIGIN_NAME: origin_name,
            CONF_ORIGIN_TRANSPORT_TYPE: origin_transport_type,
            CONF_DESTINATION_ID: destination_id,
            CONF_DESTINATION_NAME: destination_name,
            CONF_DESTINATION_TRANSPORT_TYPE: destination_transport_type,
            CONF_TRIP_WAIT_TIME: trip_wait_time,
            CONF_TRIPS_TO_CREATE: trips_to_create,
            CONF_INCLUDE_REALTIME_LOCATION: include_realtime_location,
            CONF_ROUTE_FILTER: route_filter,
            CONF_ALERTS_SENSOR: include_alerts,
            CONF_ALERT_SEVERITY: alert_severity,
            CONF_ALERT_TYPES: alert_types
            }

        subentry_data.update(sensor_options)

        return api_key, ConfigSubentryData(data = subentry_data, subentry_type = SUBENTRY_TYPE_JOURNEY, title = f"{origin_name} to {destination_name}", unique_id = f"{origin_id}_{destination_id}")

    except:
        return api_key, None
        
async def async_setup(hass: HomeAssistant, config):

    # Check if there's an old YAML config to import...
    yaml_data = defaultdict(list)

    # Iterate through and capture the data for each existing entry, grouped by API key
    # These will be converted to a single entry per API key, with multiple subentries
    for sensor in config['sensor']:
        if sensor['platform'] == DOMAIN:
            api_key, subentry_data = await get_migration_data(hass, sensor)
            if subentry_data is not None:
                yaml_data[api_key].append(subentry_data)

    if yaml_data is not None:
        # We've got a list of unique API keys (probably just the one, TBH), so let's create the entries for them
        for api_key in yaml_data:
            data = {CONF_API_KEY: api_key, CONF_SCAN_INTERVAL: 120, 'subentry_data': yaml_data[api_key]}

            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data = data
                )
            )

    return True
    

async def async_setup_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Set up Example Integration from a config entry."""

    # Initialise the coordinator that manages data updates
    coordinator = TransportNSWCoordinator(hass, config_entry)

    # Add the coordinator and update listener to config runtime data to make
    # it accessible throughout the integration
    config_entry.runtime_data = RuntimeData(coordinator)

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Return true to denote a successful setup.
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload platforms and return result
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
