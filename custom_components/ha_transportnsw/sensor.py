"""Support for Transport NSW (AU) to query next leave event."""
from datetime import datetime, timezone, timedelta
import time
import logging
import json

from TransportNSWv2 import TransportNSWv2
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_API_KEY,
    CONF_NAME,
    UnitOfTime,
    ATTR_LATITUDE,
    ATTR_LONGITUDE
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_ORIGIN_ID = 'origin_id'
CONF_DESTINATION_ID = 'destination_id'
CONF_TRIP_WAIT_TIME = 'trip_wait_time'
CONF_TRANSPORT_TYPE = 'transport_type'
CONF_STRICT_TRANSPORT_TYPE = 'strict_transport_type'
CONF_RETURN_INFO = 'return_info'
CONF_TRIPS_TO_CREATE = 'trips_to_create'
CONF_ROUTE_FILTER = 'route_filter'
CONF_INCLUDE_REALTIME_LOCATION = 'include_realtime_location'
CONF_INCLUDE_ALERTS= 'include_alerts'
CONF_ALERT_TYPES = 'alert_types'

CONF_RETURN_INFO_DEFAULT = 'medium'
CONF_ALERT_TYPES_DEFAULT = ['lineInfo', 'stopInfo', 'routeInfo', 'stopBlocking', 'bannerInfo']
CONF_ROUTE_FILTER_DEFAULT = ''
CONF_INCLUDE_ALERTS_DEFAULT = 'none'

ATTR_DUE_IN = 'due in'
ATTR_ORIGIN_STOP_ID = 'origin_stop_id'
ATTR_ORIGIN_NAME = 'origin_name'
ATTR_ORIGIN_DETAIL = 'origin_detail'
ATTR_DEPARTURE_TIME = 'departure_time'

ATTR_DESTINATION_STOP_ID = 'destination_stop_id'
ATTR_DESTINATION_NAME = 'destination_name'
ATTR_DESTINATION_DETAIL = 'destination_detail'
ATTR_ARRIVAL_TIME = 'arrival_time'

ATTR_ORIGIN_TRANSPORT_TYPE = 'origin_transport_type'
ATTR_ORIGIN_TRANSPORT_NAME = 'origin_transport_name'

ATTR_ORIGIN_LINE_NAME = 'origin_line_name'
ATTR_ORIGIN_LINE_NAME_SHORT = 'short_origin_line_name'

ATTR_OCCUPANCY = 'occupancy'
ATTR_CHANGES = 'changes'

ATTR_REAL_TIME_TRIP_ID = 'real_time_trip_id'

ATTR_ALERTS = 'alerts'

ATTRIBUTION = "Data provided by Transport NSW"
DEFAULT_NAME = "TBD" #Will be based on the origina and destination IDs by default

ICONS = {
    "Train": "mdi:train",
    "Metro": "mdi:train-variant",
    "Lightrail": "mdi:tram",
    "Light rail": "mdi:tram",
    "Bus": "mdi:bus",
    "Coach": "mdi:bus",
    "Ferry": "mdi:ferry",
    "Schoolbus": "mdi:bus",
    "School bus": "mdi:bus",
    "n/a": "mdi:clock",
    None: "mdi:clock"
}

SCAN_INTERVAL = timedelta(seconds=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ORIGIN_ID): cv.string,
        vol.Required(CONF_DESTINATION_ID): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TRIP_WAIT_TIME, default=0): cv.positive_int,
        vol.Optional(CONF_TRANSPORT_TYPE, default=0): cv.positive_int,
        vol.Optional(CONF_STRICT_TRANSPORT_TYPE, default=False): cv.boolean,
        vol.Optional(CONF_RETURN_INFO, default=CONF_RETURN_INFO_DEFAULT): vol.In(['brief', 'medium', 'verbose']),
        vol.Optional(CONF_TRIPS_TO_CREATE, default=1): vol.Range(min=1, max=6),
        vol.Optional(CONF_ROUTE_FILTER, default=CONF_ROUTE_FILTER_DEFAULT): cv.string,
        vol.Optional(CONF_INCLUDE_REALTIME_LOCATION, default=True): cv.boolean,
        vol.Optional(CONF_INCLUDE_ALERTS, default=CONF_INCLUDE_ALERTS_DEFAULT): vol.In(['none', 'verylow', 'low', 'normal', 'high', 'veryhigh']),
        vol.Optional(CONF_ALERT_TYPES, default=CONF_ALERT_TYPES_DEFAULT): vol.All(cv.ensure_list, vol.All(['lineInfo', 'routeInfo', 'stopInfo', 'stopBlocking', 'bannerInfo']))
    }
)

def convert_date(utc_string):
    temp_date = datetime.strptime(utc_string, '%Y-%m-%dT%H:%M:%SZ')
    now_timestamp = time.time()
    temp_date = temp_date + (datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp))
    return temp_date.strftime('%Y-%m-%dT%H:%M:%S')


def get_specific_platform(location_info, transport_type):
    if (transport_type == "Train" or transport_type == "Metro"):
        return location_info.split(", ")[1]
    elif transport_type == "Ferry":
        tmpLen = len(location_info.split(", "))
        if tmpLen == 4:
            return location_info.split(", ")[1] + ", " + location_info.split(", ")[2]
        elif tmpLen == 3:
            #return location_info.split(", ")[0] + ", " + location_info.split(", ")[1]
            return location_info.split(", ")[1]
        elif tmpLen == 2:
            return location_info.split(", ")[1]
        else:
            return location_info.split(", ")[0]
    elif transport_type == "Bus":
        return location_info.split(", ")[0]
    elif transport_type == "Light rail":
        tmpFind = location_info.find(" Light Rail")
        if tmpFind == -1:
            return location_info
        else:
            return location_info[: tmpFind]
    else:
        return location_info


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Transport NSW sensor."""
    origin_id = config[CONF_ORIGIN_ID]
    destination_id = config[CONF_DESTINATION_ID]
    api_key = config[CONF_API_KEY]

    if config[CONF_NAME] == 'TBD':
        config[CONF_NAME] = origin_id + "_to_" + destination_id
    name = config[CONF_NAME]

    trip_wait_time = config[CONF_TRIP_WAIT_TIME]
    transport_type = config[CONF_TRANSPORT_TYPE]
    strict_transport_type = config[CONF_STRICT_TRANSPORT_TYPE]
    return_info = config[CONF_RETURN_INFO]
    trips_to_create = config[CONF_TRIPS_TO_CREATE]
    route_filter = config[CONF_ROUTE_FILTER]
    include_realtime_location  = config[CONF_INCLUDE_REALTIME_LOCATION]
    include_alerts  = config[CONF_INCLUDE_ALERTS]
    alert_types = config[CONF_ALERT_TYPES] # It's a list

    sensor_list = []

    # Convert the alert_types into a pipe-separated string
    alert_type_full = '|'.join (alert_types)

    for trip in range (0, trips_to_create, 1):
        if trips_to_create == 1:
            name_suffix = ""
        else:
            name_suffix = "_trip_" + str(trip + 1)
        
        data = PublicTransportData(origin_id, destination_id, api_key, trip_wait_time, return_info, transport_type, strict_transport_type, route_filter, include_realtime_location, include_alerts, alert_type_full, trip)
        sensor_list.append (TransportNSWv2Sensor(data, name + name_suffix, trip, return_info))

    add_entities(sensor_list, True)


class TransportNSWv2Sensor(Entity):
    """Implementation of a Transport NSW sensor."""

    def __init__(self, data, name, index, return_info):
        """Initialize the sensor."""
        self.data = data
        self._name = name
        self._times = None
        self._return_info = return_info
        self._index = index
        self._state = None
        self._icon = ICONS[None]
        self._alerts = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self._name
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self._times is not None:
            attrTemp = {
                    ATTR_DUE_IN: self._times[ATTR_DUE_IN],
                    ATTR_ARRIVAL_TIME: self._times[ATTR_ARRIVAL_TIME],
                    ATTR_CHANGES: self._times[ATTR_CHANGES]
                }

            if self._return_info == 'medium' or self._return_info == 'verbose':
                attrTemp.update({
                    ATTR_ORIGIN_NAME: self._times[ATTR_ORIGIN_NAME],
                    ATTR_ORIGIN_DETAIL: self._times[ATTR_ORIGIN_DETAIL],
                    ATTR_DEPARTURE_TIME: self._times[ATTR_DEPARTURE_TIME],
                    ATTR_DESTINATION_NAME: self._times[ATTR_DESTINATION_NAME],
                    ATTR_DESTINATION_DETAIL: self._times[ATTR_DESTINATION_DETAIL],
                    ATTR_OCCUPANCY: self._times[ATTR_OCCUPANCY]
                })

            if self._return_info == 'verbose':
                attrTemp.update({
                    ATTR_ORIGIN_LINE_NAME: self._times[ATTR_ORIGIN_LINE_NAME],
                    ATTR_ORIGIN_LINE_NAME_SHORT: self._times[ATTR_ORIGIN_LINE_NAME_SHORT],
                    ATTR_ORIGIN_TRANSPORT_TYPE: self._times[ATTR_ORIGIN_TRANSPORT_TYPE],
                    ATTR_ORIGIN_TRANSPORT_NAME: self._times[ATTR_ORIGIN_TRANSPORT_NAME],
                    ATTR_REAL_TIME_TRIP_ID: self._times[ATTR_REAL_TIME_TRIP_ID]
                })

#            if self._include_realtime_location == True:
            attrTemp.update({
                ATTR_LATITUDE: self._times[ATTR_LATITUDE],
                ATTR_LONGITUDE: self._times[ATTR_LONGITUDE]
            })

#            if self._include_alerts == True:
            attrTemp.update({
                ATTR_ALERTS: self._times[ATTR_ALERTS]
            })

            return attrTemp;
        else:
            return {};

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return UnitOfTime.MINUTES

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    def update(self):
        """Get the latest data from Transport NSW and update the states."""
        self.data.update()
        self._times = self.data.info
        self._state = self._times[ATTR_DUE_IN]
        self._icon = ICONS[self._times[ATTR_ORIGIN_TRANSPORT_TYPE]]

class PublicTransportData:
    """The Class for handling the data retrieval."""

    def __init__(self, origin_id, destination_id, api_key, trip_wait_time, return_info, transport_type, strict_transport_type, route_filter, include_realtime_location, include_alerts, alert_type_full, index):
        """Initialize the data object."""
        self._origin_id = origin_id
        self._destination_id = destination_id
        self._api_key = api_key
        self._trip_wait_time = trip_wait_time
        self._transport_type = transport_type
        self._return_info = return_info
        self._strict_transport_type = strict_transport_type
        self._route_filter = route_filter
        self._include_realtime_location = include_realtime_location
        self._include_alerts = include_alerts
        self._alert_type_full = alert_type_full
        self._index = index
        self._attr = {}
        self.info = {
            ATTR_DUE_IN: "n/a",
            ATTR_ORIGIN_STOP_ID: "n/a",
            ATTR_ORIGIN_NAME: "n/a",
            ATTR_ORIGIN_DETAIL: "n/a",
            ATTR_DEPARTURE_TIME: "n/a",
            ATTR_DESTINATION_STOP_ID: "n/a",
            ATTR_DESTINATION_NAME: "n/a",
            ATTR_DESTINATION_DETAIL: "n/a",
            ATTR_ARRIVAL_TIME: "n/a",
            ATTR_ORIGIN_TRANSPORT_TYPE: "n/a",
            ATTR_ORIGIN_TRANSPORT_NAME: "n/a",
            ATTR_ORIGIN_LINE_NAME: "n/a",
            ATTR_ORIGIN_LINE_NAME_SHORT: "n/a",
            ATTR_OCCUPANCY: "n/a",
            ATTR_CHANGES: "n/a",
            ATTR_REAL_TIME_TRIP_ID: "n/a",
            ATTR_LATITUDE: "n/a",
            ATTR_LONGITUDE: "n/a",
            ATTR_ALERTS: "n/a"
        }
        self.tnsw = TransportNSWv2()


    def update(self):
        try:
            """Get the next leave times."""
            _data = json.loads(self.tnsw.get_trip(
                name_origin = self._origin_id, name_destination = self._destination_id, api_key = self._api_key, \
                journey_wait_time = self._trip_wait_time, transport_type = self._transport_type, strict_transport_type = self._strict_transport_type, \
                raw_output = False, route_filter = self._route_filter, journeys_to_return = 6, include_realtime_location = self._include_realtime_location, \
                include_alerts = self._include_alerts, alert_type = self._alert_type_full)
                )

            """ Fix this - use len to determine how many trips were returned?  How is that better/more elegant than catching the error?  hmm """
            """ We can't be entirely sure of how many trips were returned, so just try and update this index and gracefully fail if it doesn't work """
            self.info = {
                ATTR_DUE_IN: _data["journeys"][self._index]["due"],
                ATTR_ORIGIN_STOP_ID: _data["journeys"][self._index]["origin_stop_id"],
                ATTR_ORIGIN_NAME: _data["journeys"][self._index]["origin_name"],
                ATTR_ORIGIN_DETAIL: get_specific_platform(_data["journeys"][self._index]["origin_name"], _data["journeys"][self._index]["origin_transport_type"]),
                ATTR_DEPARTURE_TIME: convert_date(_data["journeys"][self._index]["departure_time"]),
                ATTR_DESTINATION_STOP_ID: _data["journeys"][self._index]["destination_stop_id"],
                ATTR_DESTINATION_NAME: _data["journeys"][self._index]["destination_name"],
                ATTR_DESTINATION_DETAIL: get_specific_platform(_data["journeys"][self._index]["destination_name"], _data["journeys"][self._index]["origin_transport_type"]),
                ATTR_ARRIVAL_TIME: convert_date(_data["journeys"][self._index]["arrival_time"]),
                ATTR_ORIGIN_TRANSPORT_TYPE: _data["journeys"][self._index]["origin_transport_type"],
                ATTR_ORIGIN_TRANSPORT_NAME: _data["journeys"][self._index]["origin_transport_name"],
                ATTR_ORIGIN_LINE_NAME: _data["journeys"][self._index]["origin_line_name"],
                ATTR_ORIGIN_LINE_NAME_SHORT: _data["journeys"][self._index]["origin_line_name_short"],
                ATTR_OCCUPANCY: _data["journeys"][self._index]["occupancy"].lower(),
                ATTR_CHANGES: _data["journeys"][self._index]["changes"],
                ATTR_REAL_TIME_TRIP_ID: _data["journeys"][self._index]["real_time_trip_id"],
                ATTR_LATITUDE: _data["journeys"][self._index]["latitude"],
                ATTR_LONGITUDE: _data["journeys"][self._index]["longitude"],
                ATTR_ALERTS: _data["journeys"][self._index]["alerts"]
            }

        except Exception as ex:
            self.info = {
                ATTR_DUE_IN: "n/a",
                ATTR_ORIGIN_STOP_ID: self._origin_id,
                ATTR_ORIGIN_NAME: "n/a",
                ATTR_ORIGIN_DETAIL: "n/a",
                ATTR_DEPARTURE_TIME: "n/a",
                ATTR_DESTINATION_STOP_ID: self._destination_id,
                ATTR_DESTINATION_NAME: "n/a",
                ATTR_DESTINATION_DETAIL: "n/a",
                ATTR_ARRIVAL_TIME: "n/a",
                ATTR_ORIGIN_TRANSPORT_TYPE: "n/a",
                ATTR_ORIGIN_TRANSPORT_NAME: "n/a",
                ATTR_ORIGIN_LINE_NAME: "n/a",
                ATTR_ORIGIN_LINE_NAME_SHORT: "n/a",
                ATTR_OCCUPANCY: "n/a",
                ATTR_CHANGES: "n/a",
                ATTR_REAL_TIME_TRIP_ID: "n/a",
                ATTR_LATITUDE: "n/a",
                ATTR_LONGITUDE: "n/a",
                ATTR_ALERTS: "n/a"
            }

    def convert_date(self, utc_string):
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        temp_date = datetime.strptime(departure_time, fmt)
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
        return  temp_date + offset
