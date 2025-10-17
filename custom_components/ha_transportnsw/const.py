"""Constants for our integration."""

DOMAIN = "ha_transportnsw"

DEFAULT_SCAN_INTERVAL = 120
MIN_SCAN_INTERVAL = 30
MAX_TRIP_WAIT_TIME = 60

# Mandatory data
CONF_ORIGIN_ID = 'origin_id'
CONF_ORIGIN_NAME = 'origin_name'
CONF_DESTINATION_ID = 'destination_id'
CONF_DESTINATION_NAME = 'destination_name'
CONF_TRIP_WAIT_TIME = 'trip_wait_time'
CONF_CREATE_REVERSE_TRIP = 'create_reverse_trip'
DEFAULT_CREATE_REVERSE_TRIP = False
#CONF_UNIQUE_KEY = 'unique_key'

# Optional settings
CONF_RETURN_INFO = 'return_info'
CONF_ORIGIN_TRANSPORT_TYPE = 'origin_transport_type'
CONF_DESTINATION_TRANSPORT_TYPE = 'destination_transport_type'
#CONF_STRICT_TRANSPORT_TYPE = 'strict_transport_type'
CONF_ROUTE_FILTER = 'route_filter'
#CONF_INCLUDE_ORIGIN_LOCATION = 'include_origin_location'
#CONF_INCLUDE_DESTINATION_LOCATION = 'include_destination_location'
CONF_ALERT_SEVERITY = 'alert_severity'
CONF_ALERT_TYPES = 'alert_types'
CONF_TRIPS_TO_CREATE = 'trips_to_create'
#SENSOR_ALERTS = 'alerts'
#SENSOR_ALERTS_NAME = 'alerts'

# Sensor key names
CONF_DUE_SENSOR = 'due'
CONF_CHANGES_SENSOR = 'changes'
CHANGES_LIST = 'changes_list'
CONF_DELAY_SENSOR = 'delay'
CONF_ALERTS_SENSOR = 'alerts'
CONF_FIRST_LEG_DEPARTURE_TIME_SENSOR = 'departure_time'
CONF_LAST_LEG_ARRIVAL_TIME_SENSOR = 'arrival_time'
CONF_ORIGIN_NAME_SENSOR = 'origin_name'
#CONF_ORIGIN_DETAIL_SENSOR = 'origin_detail'
CONF_FIRST_LEG_LINE_NAME_SENSOR = 'origin_line_name'
CONF_FIRST_LEG_LINE_NAME_SHORT_SENSOR = 'origin_line_name_short'
CONF_FIRST_LEG_TRANSPORT_TYPE_SENSOR = 'origin_transport_type'
CONF_FIRST_LEG_TRANSPORT_NAME_SENSOR = 'origin_transport_name'
CONF_FIRST_LEG_OCCUPANCY_SENSOR = 'origin_occupancy'
CONF_FIRST_LEG_DEVICE_TRACKER = 'first_leg_device_tracker'
CONF_DESTINATION_NAME_SENSOR = 'destination_name'
#CONF_DESTINATION_DETAIL_SENSOR = 'destination_detail'
CONF_LAST_LEG_LINE_NAME_SENSOR = 'destination_line_name'
CONF_LAST_LEG_LINE_NAME_SHORT_SENSOR = 'destination_line_name_short'
CONF_LAST_LEG_TRANSPORT_TYPE_SENSOR = 'destination_transport_type'
CONF_LAST_LEG_TRANSPORT_NAME_SENSOR = 'destination_transport_name'
CONF_LAST_LEG_OCCUPANCY_SENSOR = 'destination_occupancy'
CONF_LAST_LEG_DEVICE_TRACKER = 'last_leg_device_tracker'
CONF_SENSOR_CREATION = 'sensor_creation'

# Sensor friendly names
CONF_DUE_FRIENDLY = 'due'
CONF_CHANGES_FRIENDLY = 'changes'
CONF_DELAY_FRIENDLY = 'delay'
CONF_ALERTS_FRIENDLY = 'alerts'
CONF_FIRST_LEG_DEPARTURE_TIME_FRIENDLY = 'departure from origin'
CONF_LAST_LEG_ARRIVAL_TIME_FRIENDLY = 'arrival at destination'
CONF_ORIGIN_NAME_FRIENDLY = 'origin name'
#CONF_ORIGIN_DETAIL_FRIENDLY = 'origin detail'
CONF_FIRST_LEG_LINE_NAME_FRIENDLY = 'first leg line name'
CONF_FIRST_LEG_LINE_NAME_SHORT_FRIENDLY = 'first leg line name (short)'
CONF_FIRST_LEG_OCCUPANCY_FRIENDLY = 'first leg occupacy'
CONF_FIRST_LEG_TRANSPORT_TYPE_FRIENDLY = 'first leg transport type'
CONF_FIRST_LEG_TRANSPORT_NAME_FRIENDLY = 'first leg transport name'
#CONF_FIRST_LEG_DEVICE_TRACKER_FRIENDLY = 'first leg device tracker'
CONF_DESTINATION_NAME_FRIENDLY = 'destination name'
#CONF_DESTINATION_DETAIL_FRIENDLY = 'destination detail'
CONF_LAST_LEG_LINE_NAME_FRIENDLY = 'last leg line name'
CONF_LAST_LEG_LINE_NAME_SHORT_FRIENDLY = 'last leg line name (short)'
CONF_LAST_LEG_OCCUPANCY_FRIENDLY = 'last leg occupancy'
CONF_LAST_LEG_TRANSPORT_TYPE_FRIENDLY = 'last leg transport type'
CONF_LAST_LEG_TRANSPORT_NAME_FRIENDLY = 'last leg transport name'
#CONF_LAST_LEG_DEVICE_TRACKER_FRIENDLY = 'last leg device_tracker'

# Sensor creation defaults
DEFAULT_TRIP_WAIT_TIME = 10
#DEFAULT_RETURN_INFO = 'none'
DEFAULT_TRANSPORT_TYPE_SELECTOR = ['Train', 'Metro', 'Light rail', 'Bus', 'Ferry']
#DEFAULT_STRICT_TRANSPORT_TYPE = False
DEFAULT_ROUTE_FILTER = ''
#DEFAULT_INCLUDE_ORIGIN_LOCATION = True
#DEFAULT_INCLUDE_DESTINATION_LOCATION = False
#DEFAULT_ALERTS = False
DEFAULT_ALERT_TYPES = ['lineinfo', 'stopinfo', 'routeinfo', 'stopblocking', 'bannerinfo']
DEFAULT_ALERT_SEVERITY = 'high'
DEFAULT_TRIPS_TO_CREATE = 1
ORIGIN_TRANSPORT_TYPE_LIST = ['Train', 'Metro', 'Light rail', 'Bus', 'Coach', 'Ferry', 'School bus', 'Walk']
DESTINATION_TRANSPORT_TYPE_LIST = ['Train', 'Metro', 'Light rail', 'Bus', 'Coach', 'Ferry', 'School bus', 'Walk']

DEFAULT_SENSOR_CREATION = 'none'
DEFAULT_CHANGES_SENSOR = False
DEFAULT_DELAY_SENSOR = False
DEFAULT_ALERTS_SENSOR = False
DEFAULT_FIRST_LEG_DEPARTURE_TIME_SENSOR = False
DEFAULT_LAST_LEG_ARRIVAL_TIME_SENSOR = False
DEFAULT_ORIGIN_NAME_SENSOR = False
#DEFAULT_ORIGIN_DETAIL_SENSOR = False
DEFAULT_FIRST_LEG_LINE_NAME_SENSOR = False
DEFAULT_FIRST_LEG_LINE_NAME_SHORT_SENSOR = False
DEFAULT_FIRST_LEG_OCCUPANCY_SENSOR = False
DEFAULT_FIRST_LEG_DEVICE_TRACKER = True
DEFAULT_DESTINATION_NAME_SENSOR = False
#DEFAULT_DESTINATION_DETAIL_SENSOR = False
DEFAULT_LAST_LEG_LINE_NAME_SENSOR = False
DEFAULT_LAST_LEG_LINE_NAME_SHORT_SENSOR = False
DEFAULT_LAST_LEG_OCCUPANCY_SENSOR = False
DEFAULT_LAST_LEG_DEVICE_TRACKER = 'if_not_duplicated'




CONF_INCLUDE_REALTIME_LOCATION = 'include_realtime_location'
CONF_ORIGIN_DEVICE_TRACKER = 'origin_device_tracker'
CONF_DESTINATION_DEVICE_TRACKER = 'destination_device_tracker'
#DEFAULT_ORIGIN_DEVICE_TRACKER = 'always'
#DEFAULT_DESTINATION_DEVICE_TRACKER = 'if_not_duplicated'

#ORIGIN_LOCATION = 'origin_location'
#DESTINATION_LOCATION = 'destination_location'
ORIGIN_LATITUDE = 'origin_latitude'
ORIGIN_LONGITUDE = 'origin_longitude'
DESTINATION_LATITUDE = 'destination_latitude'
DESTINATION_LONGITUDE = 'destination_longitude'

#DEFAULT_DESTINATION_LINE_NAME = False
#DEFAULT_DESTINATION_LINE_NAME_SHORT = False
#DEFAULT_DESTINATION_TRANSPORT_TYPE = False
       


# # Optional sensor groupings

# BASIC_SENSORS = [
                    # CONF_CREATE_ARRIVAL_TIME, CONF_CREATE_DEPARTURE_TIME, CONF_CREATE_CHANGES
                # ]

# MEDIUM_SENSORS = [
                    # CONF_CREATE_ORIGIN_NAME, CONF_CREATE_DESTINATION_NAME,
                    # CONF_CREATE_ORIGIN_OCCUPANCY, CONF_CREATE_DESTINATION_OCCUPANCY
                # ]

# VERBOSE_SENSORS = [
                    # CONF_CREATE_ORIGIN_LINE_NAME, CONF_CREATE_ORIGIN_LINE_NAME_SHORT,
                    # CONF_CREATE_DESTINATION_LINE_NAME, CONF_CREATE_DESTINATION_LINE_NAME_SHORT,
                    # CONF_CREATE_ORIGIN_TRANSPORT_TYPE, CONF_CREATE_ORIGIN_TRANSPORT_NAME,
                    # CONF_CREATE_DESTINATION_TRANSPORT_TYPE, CONF_CREATE_DESTINATION_TRANSPORT_NAME
                # ]



# CONF_JOURNEY_SENSORS = [
                        # CONF_DEPARTURE_TIME, CONF_ARRIVAL_TIME,
                        # CONF_DESTINATION_NAME, CONF_ORIGIN_OCCUPANCY,
                        # CONF_CHANGES
                    # ]
# ORIGIN_SENSORS = [
                    # CONF_ORIGIN_LINE_NAME, CONF_ORIGIN_LINE_NAME_SHORT,
                    # CONF_ORIGIN_TRANSPORT_TYPE, CONF_ORIGIN_TRANSPORT_NAME
                # ]

# # DESTINATION_SENSORS = [
                        # # CONF_DESTINATION_LINE_NAME, CONF_DESTINATION_LINE_NAME_SHORT,
                        # # CONF_DESTINATION_TRANSPORT_TYPE, CONF_DESTINATION_TRANSPORT_NAME,
                        # # CONF_DESTINATION_TRACKER, CONF_DESTINATION_OCCUPANCY
                    # # ]

# DESTINATION_SENSORS = {
                    # CONF_DESTINATION_LINE_NAME: [CONF_DESTINATION_LINE_NAME_FRIENDLY, DEFAULT_DESTINATION_LINE_NAME],
                    # CONF_DESTINATION_LINE_NAME_SHORT: [CONF_DESTINATION_LINE_NAME_SHORT_FRIENDLY, DEFAULT_DESTINATION_LINE_NAME_SHORT],
                    # CONF_DESTINATION_TRANSPORT_TYPE: [CONF_DESTINATION_TRANSPORT_TYPE_FRIENDLY, DEFAULT_DESTINATION_TRANSPORT_TYPE],
                    # CONF_DESTINATION_TRANSPORT_NAME: [CONF_DESTINATION_TRANSPORT_NAME_FRIENDLY, DEFAULT_DESTINATION_TRANSPORT_NAME],
                    # CONF_DESTINATION_OCCUPANCY: [CONF_DESTINATION_OCCUPANCY_FRIENDLY, DEFAULT_DESTINATION_OCCUPANCY],
                    # CONF_DESTINATION_TRACKER: [CONF_DESTINATION_TRACKER_FRIENDLY, DEFAULT_DESTINATION_TRACKER]
                    # }
       


# CONF_CREATE_LOCATION_DETAIL ='create_location_detail_sensors'
# DEFAULT_CREATE_LOCATION_DETAIL = False
# CONF_CREATE_LINE_NAME_DETAIL ='create_line_name_detail_sensors'
# DEFAULT_CREATE_LINE_NAME_DETAIL = False

# ATTR_DUE_IN = 'due'
# ATTR_DELAY = 'delay'
# ATTR_ORIGIN_STOP_ID = 'origin_stop_id'
# ATTR_ORIGIN_NAME = 'origin_name'
# ATTR_ORIGIN_DETAIL = 'origin_detail'
# ATTR_DEPARTURE_TIME = 'departure_time'

# ATTR_DESTINATION_STOP_ID = 'destination_stop_id'
# ATTR_DESTINATION_NAME = 'destination_name'
# ATTR_DESTINATION_DETAIL = 'destination_detail'
# ATTR_ARRIVAL_TIME = 'arrival_time'

# ATTR_ORIGIN_TRANSPORT_TYPE = 'origin_transport_type'
# ATTR_ORIGIN_TRANSPORT_NAME = 'origin_transport_name'

# ATTR_ORIGIN_LINE_NAME = 'origin_line_name'
# ATTR_ORIGIN_LINE_NAME_SHORT = 'short_origin_line_name'

# ATTR_OCCUPANCY = 'occupancy'
# ATTR_CHANGES = 'changes'

# ATTR_REAL_TIME_TRIP_ID = 'real_time_trip_id'
# ATTR_AVMS_TRIP_ID = 'avms_trip_id'

# ATTR_ALERTS = 'alerts'

ATTRIBUTION = "Data provided by Transport NSW"
#DEFAULT_NAME = "TBD" #Will be based on the origina and destination IDs by default

# #Sensors
# SENSOR_DUE = 'due'
# SENSOR_DUE_NAME = 'due'
# SENSOR_ARRIVAL_TIME = 'arrival_time'
# SENSOR_ARRIVAL_TIME_NAME = 'arrival time'
# SENSOR_DEPARTURE_TIME = 'departure_time'
# SENSOR_DEPARTURE_TIME_NAME = 'departure time'
# SENSOR_DELAY = 'delay'
# SENSOR_DELAY_NAME = 'delay'
# SENSOR_OCCUPANCY = 'occupancy'
# SENSOR_OCCUPANCY_NAME = 'occupancy'
# SENSOR_CHANGES = 'changes'
# SENSOR_CHANGES_NAME = 'changes'

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
    None: "mdi:train"
}

OCCUPANCY_ICONS = {
    "MANY_SEATS": ["mdi:account", "Many seats"],
    "FEW_SEATS": ["mdi:account-multiple", "Few seats"],
    "STANDING_ONLY": ["mdi:account-group","Standing only"],
    "Unknown": ["mdi:account-question", "Unknown"],
    "Unavailable": ["mdi:account-question", "Unavailable"],
    None: ["mdi:account-question", "Unknown"]
}

TRANSPORT_TYPE = {
    "All": 0,
    "Train": 1,
    "Metro": 2,
    "Light rail": 4,
    "Bus": 5,
    "Coach": 7,
    "Ferry": 9,
    "School bus": 11,
    "Walk": 99
}

ALERT_PRIORITIES = {
    "verylow"  : 1,
    "low"      : 2,
    "normal"   : 3,
    "high"     : 4,
    "veryhigh" : 5
}
 
SUBENTRY_TYPE_JOURNEY = 'subentry_journey'
#SUBENTRY_JOURNEYPART = 'subentry_journeypart'
API_CALLS = 'api_calls'
API_CALLS_NAME = 'API calls'
STOP_TEST_ID = '200060' # Central station
