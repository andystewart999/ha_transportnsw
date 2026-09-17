"""Constants for the Transport NSW Mk II integration"""

# import json
# from pathlib import Path

DOMAIN = "ha_transportnsw"
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30

# API-related constants
API_CALLS = "api_calls"
API_DAILY_LIMIT = 60000
AVERAGE_CALLS_PER_JOURNEY = 3
AVERAGE_API_CALLS = "average_api_calls"
AVERAGE_API_CALLS_WINDOW = 5
STORAGE_VERSION = 1

# Config-entry sensor names
API_CALLS_SENSOR = "api_calls"
API_CALLS_FRIENDLY = "API calls"
AVERAGE_API_CALLS_SENSOR = "average_api_calls"
AVERAGE_API_CALLS_FRIENDLY = "Average API calls per poll"

# Subentry settings
CONF_ORIGIN_TYPE = "origin_type"
CONF_ORIGIN_ID = "origin_id"
CONF_ORIGIN_NAME = "origin_name"
CONF_DESTINATION_ID = "destination_id"
CONF_DESTINATION_NAME = "destination_name"
CONF_TRIP_WAIT_TIME = "trip_wait_time"
DEFAULT_TRIP_WAIT_TIME = 10
CONF_CREATE_REVERSE_TRIP = "create_reverse_trip"
DEFAULT_CREATE_REVERSE_TRIP = False
CONF_RETURN_INFO = "return_info"
CONF_ORIGIN_TRANSPORT_TYPE = "origin_transport_type"
CONF_DESTINATION_TRANSPORT_TYPE = "destination_transport_type"
CONF_RUN_FILTER = "run_filter"
CONF_ROUTE_FILTER = "route_filter"
CONF_MAX_CHANGES = "max_changes"
CONF_ALERTS_SENSOR = "alerts"
CONF_ALERT_SEVERITY = "alert_severity"
CONF_ALERT_TYPES = "alert_types"

# Subentry sensor names
DUE_SENSOR = "due"
DUE_FRIENDLY = "due"
POLLING_SENSOR = "polling"
POLLING_FRIENDLY = "poll status"
CHANGES_SENSOR = "changes"
CHANGES_FRIENDLY = "changes"
DELAY_SENSOR = "delay"
DELAY_FRIENDLY = "delay"
DURATION_SENSOR = "duration"
DURATION_FRIENDLY = "duration"
ALERTS_SENSOR = "alerts"
ALERTS_FRIENDLY = "alerts"
FIRST_LEG_DEPARTURE_TIME_SENSOR = "departure_time"
FIRST_LEG_DEPARTURE_TIME_FRIENDLY = "departure from origin"
LAST_LEG_ARRIVAL_TIME_SENSOR = "arrival_time"
LAST_LEG_ARRIVAL_TIME_FRIENDLY = "arrival at destination"
ORIGIN_NAME_SENSOR = "origin_name"
ORIGIN_NAME_FRIENDLY = "origin name"
ORIGIN_DETAIL_SENSOR = "origin_detail"
ORIGIN_DETAIL_FRIENDLY = "origin detail"
FIRST_LEG_LINE_NAME_SENSOR = "origin_line_name"
FIRST_LEG_LINE_NAME_FRIENDLY = "first leg line name"
FIRST_LEG_LINE_NAME_SHORT_SENSOR = "origin_line_name_short"
FIRST_LEG_LINE_NAME_SHORT_FRIENDLY = "first leg line name (short)"
FIRST_LEG_RUN_NAME_SENSOR = "origin_run_name"
FIRST_LEG_RUN_NAME_FRIENDLY = "first leg run name"
FIRST_LEG_TRANSPORT_TYPE_SENSOR = "origin_transport_type"
FIRST_LEG_TRANSPORT_TYPE_FRIENDLY = "first leg transport type"
FIRST_LEG_TRANSPORT_NAME_SENSOR = "origin_transport_name"
FIRST_LEG_TRANSPORT_NAME_FRIENDLY = "first leg transport name"
FIRST_LEG_OCCUPANCY_SENSOR = "origin_occupancy"
FIRST_LEG_OCCUPANCY_FRIENDLY = "first leg occupancy"
FIRST_LEG_OCCUPANCY_DETAIL_SENSOR = "origin_occupancy_detail"
FIRST_LEG_OCCUPANCY_DETAIL_FRIENDLY = "first leg occupancy detail"
FIRST_LEG_TRAIN_SET_SENSOR = "origin_train_set"
FIRST_LEG_TRAIN_SET_FRIENDLY = "first leg vehicle set"
DESTINATION_NAME_SENSOR = "destination_name"
DESTINATION_NAME_FRIENDLY = "destination name"
DESTINATION_DETAIL_SENSOR = "destination_detail"
DESTINATION_DETAIL_FRIENDLY = "destination detail"
LAST_LEG_LINE_NAME_SENSOR = "destination_line_name"
LAST_LEG_LINE_NAME_FRIENDLY = "last leg line name"
LAST_LEG_LINE_NAME_SHORT_SENSOR = "destination_line_name_short"
LAST_LEG_LINE_NAME_SHORT_FRIENDLY = "last leg line name (short)"
LAST_LEG_RUN_NAME_SENSOR = "destination_run_name"
LAST_LEG_RUN_NAME_FRIENDLY = "last leg run name"
LAST_LEG_TRANSPORT_TYPE_SENSOR = "destination_transport_type"
LAST_LEG_TRANSPORT_TYPE_FRIENDLY = "last leg transport type"
LAST_LEG_TRANSPORT_NAME_SENSOR = "destination_transport_name"
LAST_LEG_TRANSPORT_NAME_FRIENDLY = "last leg transport name"
LAST_LEG_OCCUPANCY_SENSOR = "destination_occupancy"
LAST_LEG_OCCUPANCY_FRIENDLY = "last leg occupancy"
LAST_LEG_OCCUPANCY_DETAIL_SENSOR = "destination_occupancy_detail"
LAST_LEG_OCCUPANCY_DETAIL_FRIENDLY = "last leg occupancy detail"
LAST_LEG_TRAIN_SET_SENSOR = "destination_train_set"
LAST_LEG_TRAIN_SET_FRIENDLY = "last leg vehicle set"
INCLUDE_REALTIME_LOCATION = "include_realtime_location"
SENSOR_CREATION = "sensor_creation"
ORIGIN_END_OF_LINE = "origin_end_of_line"
DESTINATION_END_OF_LINE = "destination_end_of_line"

ALL_TRANSPORT_TYPES = [
    "1",
    "2",
    "4",
    "5",
    "7",
    "9",
    "11",
    "99",
]
DEFAULT_TRANSPORT_TYPE = ["1", "2", "4", "5", "9"]

# Changes info
ATTR_CHANGES_LIST = "changes_list"
ATTR_LOCATIONS_LIST = "locations_list"

# Sensor defaults
DEFAULT_RUN_FILTER = ""
DEFAULT_ROUTE_FILTER = ""
DEFAULT_MAX_CHANGES = 2
DEFAULT_ALERT_TYPES = [
    "lineinfo",
    "stopinfo",
    "routeinfo",
    "stopblocking",
    "bannerinfo",
]
DEFAULT_ALERT_SEVERITY = "high"
DEFAULT_SENSOR_CREATION = "none"
DEFAULT_ALERTS_SENSOR = False

# SubentryFlow defaults
MAX_TRIP_WAIT_TIME = 60
MAX_MAX_CHANGES = 5

# Transport for NSW constants
TFNSW_ATTRIBUTION = "Data provided by Transport NSW"
TFNSW_REGISTRATION = "https://opendata.transport.nsw.gov.au/data/user/register"
TFNSW_STOPFINDER = "https://transportnsw.info/routes/"

# Subentry stuff
SUBENTRY_TYPE_JOURNEY = "subentry_journey"
STOP_TEST_ID = "200060"  # Central station

# Lookups and mapping dictionaries
JOURNEY_ICONS = {
    "Train": "mdi:train",
    "Metro": "mdi:train-variant",
    "Lightrail": "mdi:tram",
    "Light rail": "mdi:tram",
    "Bus": "mdi:bus",
    "Coach": "mdi:bus",
    "Ferry": "mdi:ferry",
    "Schoolbus": "mdi:bus",
    "School bus": "mdi:bus",
    "Walk": "mdi:walk",
    "n/a": "mdi:train",
    "unavailable": "mdi:train",
    None: "mdi:train",
}


# Oh I wish TfNSW would be more consistent with their constants...
OCCUPANCY_ICONS = {
    "MANY_SEATS": ["mdi:account", "Many seats"],
    "MANY_SEATS_AVAILABLE": ["mdi:account", "Many seats"],
    "FEW_SEATS": ["mdi:account-multiple", "Few seats"],
    "FEW_SEATS_AVAILABLE": ["mdi:account-multiple", "Few seats"],
    "STANDING_ONLY": ["mdi:account-group", "Standing room"],
    "STANDING_ROOM_ONLY": ["mdi:account-group", "Standing room"],
    "CRUSHED_STANDING_ROOM_ONLY": ["mdi:account-group", "Crushed standing room"],
    "FULL": ["mdi:account-group", "Full"],
    "Unknown": ["mdi:account-question", "Unknown"],
    "Unavailable": ["mdi:account-question", "Unavailable"],
    None: ["mdi:account-question", "Unknown"],
}

OCCUPANCY_DETAIL_GLYPHS = {
    0: "⬜",
    1: "🟩",
    2: "🟨",
    3: "🟥",
}

TRANSPORT_TYPE = {
    1: "Train",
    2: "Metro",
    4: "Light rail",
    5: "Bus",
    7: "Coach",
    9: "Ferry",
    11: "School bus",
    99: "Walk",
    100: "Walk",
}

ALERT_PRIORITIES = {
    "none": 0,
    "verylow": 1,
    "low": 2,
    "normal": 3,
    "high": 4,
    "veryhigh": 5,
}

__all__ = [name for name in globals() if name.isupper()]
