"""Helper functions for TransportNSWv2 API"""
from TransportNSWv2 import TransportNSWv2, InvalidAPIKey, APIRateLimitExceeded, StopError, TripError
import logging
from typing import List
import json
from pathlib import Path
import pytz
import tzlocal
import time
from datetime import date, datetime

_LOGGER = logging.getLogger(__name__)

from .const import *

def convert_date(utc_string) -> datetime:
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    #fmt = '%H:%M:%SZ'
    
    utc_dt = datetime.strptime(utc_string, fmt)
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)
    local_timezone = tzlocal.get_localzone()
    local_dt = utc_dt.astimezone(local_timezone)
    
    return local_dt

def get_trips (api_key: str, name_origin: str, name_destination: str, journey_wait_time: int = 0, origin_transport_type: int = [0], destination_transport_type: int = [0],
              strict_transport_type: bool = False, route_filter: str = '', journeys_to_return: int = 1, include_realtime_location: bool = True, 
              include_alerts: bool = False, alert_severity: str = 'high', alert_type: str = ['all']):
    # Use the Transport NSW API to request trip information
    # Exceptions will be caught by the calling function

    if not include_alerts:
        # A bit hacky, I'll publish an updated version of PyTransportNSWv2 to fix this soon
        alert_severity = 'none'

    tfnsw = TransportNSWv2()
    data = tfnsw.get_trip (api_key = api_key, name_origin = name_origin, name_destination = name_destination, journey_wait_time = journey_wait_time,
        origin_transport_type = origin_transport_type, destination_transport_type = destination_transport_type, strict_transport_type = strict_transport_type, raw_output = False,
        route_filter = route_filter, journeys_to_return = journeys_to_return, include_realtime_location = include_realtime_location,
        include_alerts = alert_severity, alert_type = alert_type, check_stop_ids = False)

    return json.loads(data)

def check_stops (api_key: str, stops: List[str]):
    # Check all provided stops using the Transport NSW API, and return all the associated stop metadata
    # Exceptions will be captured by the calling function

    try:
        tfnsw = TransportNSWv2()
        data = tfnsw.check_stops (api_key = api_key, stops = stops)
    
        return data

    except InvalidAPIKey:
        raise InvalidAPIKey
    
    except APIRateLimitExceeded:
        raise APIRateLimitExceeded
    
    except StopError:
        raise StopError
    
    except Exception as ex:
        raise StopError

def get_stop_detail (stop_data, stop_id: str, property: str):
    # Return a specific property from the provided stop metadata

    try:
        stop_detail = "n/a"

        for stop in stop_data['stop_list']:
            if stop['stop_id'] == stop_id:
                stop_detail = stop['stop_detail']['disassembledName']
                break

        return stop_detail
        
    except Exception as ex:
        return "n/a"


def set_optional_sensors (sensor_data: str):
    # Determine which optional sensors to create
    sensor_data = sensor_data.lower()

    # First reset what sensors we're creating
    for sensor_group in [BASIC_SENSORS, MEDIUM_SENSORS, VERBOSE_SENSORS]:
        for sensor in sensor_group:
            sensor = False
    
    # Then turn specific pre-defined sensor groups back on based on what the user selected
    if sensor_data == 'basic':
        for sensor_group in [BASIC_SENSORS]:
            for sensor in sensor_group:
                sensor = True
    
    elif sensor_data == 'medium':
        for sensor_group in [BASIC_SENSORS, MEDIUM_SENSORS]:
            for sensor in sensor_group:
                sensor = True
    
    elif return_data == 'verbose':
        for sensor_group in [BASIC_SENSORS, MEDIUM_SENSORS, VERBOSE_SENSORS]:
            for sensor in sensor_group:
                sensor = True


def get_api_calls (file_path: str) -> int:
    # Get the current date first
    try:
        api_info = json.loads(
                Path(file_path).read_text(encoding="utf8")
            )

        return api_info[API_CALLS]

    except Exception as ex:
        return 0


def set_api_calls (file_path: str, api_calls: int) -> int:
    # Get the current date
    try:
        api_info = json.loads(
                Path(file_path).read_text(encoding="utf8")
            )
    
    except:
        api_info = {}

    current_date = datetime.now().date()
    # Do we need to reset the API counter?
    if 'last_reset_date' in api_info:
        # Check the date
        last_reset_date = datetime.strptime(api_info['last_reset_date'], '%Y-%m-%d').date()

        if current_date > last_reset_date:
            api_calls = 0
            last_reset_date = current_date
    else:
        # Assume it's the first time starting up
        last_reset_date = current_date

    data = {
        API_CALLS: api_calls,
        'last_reset_date': str(last_reset_date)
    }

    # Store the current API calls value peristently
    Path(file_path).write_text(json.dumps(data), encoding="utf8")

    return api_calls
        
    
    