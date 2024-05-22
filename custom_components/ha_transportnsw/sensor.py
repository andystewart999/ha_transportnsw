"""Support for Transport NSW (AU) to query next leave event."""
from datetime import datetime, timezone, timedelta
import time
import logging
import json

from TransportNSW import TransportNSW
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
CONF_RETURN_INFO = 'return_info'

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

ATTRIBUTION = "Data provided by Transport NSW"
DEFAULT_NAME = "Next Journey"

ICONS = {
    "Train": "mdi:train",
    "Lightrail": "mdi:tram",
    "Light rail": "mdi:tram",
    "Bus": "mdi:bus",
    "Coach": "mdi:bus",
    "Ferry": "mdi:ferry",
    "Schoolbus": "mdi:bus",
    "School bus": "mdi:bus",
    "n/a": "mdi:clock",
    "Walk": "mdi:walk",
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
        vol.Optional(CONF_RETURN_INFO, default='medium'): vol.In(['brief', 'medium', 'verbose'])
    }
)


def convert_date(utc_string):
    temp_date = datetime.strptime(utc_string, '%Y-%m-%dT%H:%M:%SZ')
    now_timestamp = time.time()
    temp_date = temp_date + (datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp))
    return temp_date.strftime('%Y-%m-%dT%H:%M:%S')


def get_specific_platform(location_info, transport_type):
    if transport_type == "Train":
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
    name = config[CONF_NAME]
    trip_wait_time = config[CONF_TRIP_WAIT_TIME]
    transport_type = config[CONF_TRANSPORT_TYPE]
    return_info = config[CONF_RETURN_INFO]

    data = PublicTransportData(origin_id, destination_id, api_key, trip_wait_time, return_info, transport_type)
    add_entities([TransportNSWSensor(data, name, return_info)], True)


class TransportNSWSensor(Entity):
    """Implementation of an Transport NSW sensor."""

    def __init__(self, data, name, return_info):
        """Initialize the sensor."""
        self.data = data
        self._name = name
        self._times = None
        self._return_info = return_info
        self._state = None
        self._icon = ICONS[None]

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
                    ATTR_CHANGES: self._times[ATTR_CHANGES],
                    ATTR_LATITUDE: self._times[ATTR_LATITUDE],
                    ATTR_LONGITUDE: self._times[ATTR_LONGITUDE]
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

    def __init__(self, origin_id, destination_id, api_key, trip_wait_time, return_info, transport_type):
        """Initialize the data object."""
        self._origin_id = origin_id
        self._destination_id = destination_id
        self._api_key = api_key
        self._trip_wait_time = trip_wait_time
        self._transport_type = transport_type
        self._return_info = return_info
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
            ATTR_LONGITUDE: "n/a"
        }
        self.tnsw = TransportNSW()

    def update(self):
        try:
            """Get the next leave time."""
            _data = json.loads(self.tnsw.get_trip(
                self._origin_id, self._destination_id, self._api_key, self._trip_wait_time, self._transport_type
                ))

            self.info = {
                ATTR_DUE_IN: _data["due"],
                ATTR_ORIGIN_STOP_ID: _data["origin_stop_id"],
                ATTR_ORIGIN_NAME: _data["origin_name"],
                ATTR_ORIGIN_DETAIL: get_specific_platform(_data["origin_name"], _data["origin_transport_type"]),
                ATTR_DEPARTURE_TIME: convert_date(_data["departure_time"]),
                ATTR_DESTINATION_STOP_ID: _data["destination_stop_id"],
                ATTR_DESTINATION_NAME: _data["destination_name"],
                ATTR_DESTINATION_DETAIL: get_specific_platform(_data["destination_name"], _data["origin_transport_type"]),
                ATTR_ARRIVAL_TIME: convert_date(_data["arrival_time"]),
                ATTR_ORIGIN_TRANSPORT_TYPE: _data["origin_transport_type"],
                ATTR_ORIGIN_TRANSPORT_NAME: _data["origin_transport_name"],
                ATTR_ORIGIN_LINE_NAME: _data["origin_line_name"],
                ATTR_ORIGIN_LINE_NAME_SHORT: _data["origin_line_name_short"],
                ATTR_OCCUPANCY: _data["occupancy"].lower(),
                ATTR_CHANGES: _data["changes"],
                ATTR_REAL_TIME_TRIP_ID: _data["real_time_trip_id"],
                ATTR_LATITUDE: _data["latitude"],
                ATTR_LONGITUDE: _data["longitude"]
            }

        except:
            _LOGGER.error("Error returning trip data")

    def convert_date(self, utc_string):
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        temp_date = datetime.strptime(departure_time, fmt)
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
        return  temp_date + offset
