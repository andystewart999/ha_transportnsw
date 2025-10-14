"""Support for Transport NSW (AU) to query next leave event (raw, single-call)."""
from datetime import datetime, timezone, timedelta
import time
import logging
import json
import re
from typing import Any, Dict, List, Optional, Union

from TransportNSWv2 import TransportNSWv2
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_API_KEY,
    CONF_NAME,
    UnitOfTime,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt as dt_util  # <-- use HA-configured timezone

_LOGGER = logging.getLogger(__name__)

# ---- Config keys
CONF_ORIGIN_ID = 'origin_id'
CONF_DESTINATION_ID = 'destination_id'
CONF_TRIP_WAIT_TIME = 'trip_wait_time'
CONF_TRANSPORT_TYPE = 'transport_type'              # Ignored by raw output (kept for compat)
CONF_STRICT_TRANSPORT_TYPE = 'strict_transport_type' # Ignored by raw output (kept for compat)
CONF_RETURN_INFO = 'return_info'
CONF_TRIPS_TO_CREATE = 'trips_to_create'
CONF_ROUTE_FILTER = 'route_filter'                  # Ignored by raw output (kept for compat)
CONF_INCLUDE_REALTIME_LOCATION = 'include_realtime_location'  # dropped
CONF_INCLUDE_ALERTS = 'include_alerts'                          # dropped
CONF_ALERT_TYPES = 'alert_types'                                  # dropped

CONF_RETURN_INFO_DEFAULT = 'medium'
CONF_ALERT_TYPES_DEFAULT = ['lineInfo', 'stopInfo', 'routeInfo', 'stopBlocking', 'bannerInfo']
CONF_ROUTE_FILTER_DEFAULT = ''
CONF_INCLUDE_ALERTS_DEFAULT = 'none'

# ---- Attribute keys (existing)
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

# ---- NEW verbose-only attributes (snake_case as requested)
ATTR_DEPARTURE_TIME_PLANNED = 'departure_time_planned'
ATTR_DEPARTURE_TIME_ESTIMATED = 'departure_time_estimated'
ATTR_STOP_SEQUENCE = 'stop_sequence'          # list[str] (stop names only)
ATTR_NUMBER_OF_CARS = 'number_of_cars'

ATTRIBUTION = "Data provided by Transport NSW"
DEFAULT_NAME = "TBD"  # Will be based on the origin and destination IDs by default

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
    None: "mdi:clock",
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
        # Kept for backwards compatibility
        vol.Optional(CONF_INCLUDE_REALTIME_LOCATION, default=False): cv.boolean,
        vol.Optional(CONF_INCLUDE_ALERTS, default=CONF_INCLUDE_ALERTS_DEFAULT): vol.In(['none', 'verylow', 'low', 'normal', 'high', 'veryhigh']),
        vol.Optional(CONF_ALERT_TYPES, default=CONF_ALERT_TYPES_DEFAULT): vol.All(cv.ensure_list, vol.All(['lineInfo', 'routeInfo', 'stopInfo', 'stopBlocking', 'bannerInfo'])),
    }
)

# ---- Helpers

def _to_local_iso_naive(zulu_or_iso: Optional[str]) -> str:
    """Use HA's timezone. If input has Z/offset, convert; if naive, assume it's already local."""
    if not zulu_or_iso or not isinstance(zulu_or_iso, str):
        return "n/a"
    try:
        s = zulu_or_iso.strip().replace(" ", "T")

        # Explicit timezone -> parse as aware and convert to HA tz
        if s.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", s):
            try:
                aware = datetime.fromisoformat(s.replace("Z", "+00:00"))
            except ValueError:
                aware = datetime.strptime(s.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            dt_local = aware.astimezone(dt_util.DEFAULT_TIME_ZONE)
        else:
            # Naive string -> it's already local
            naive_local = datetime.fromisoformat(s)
            dt_local = naive_local.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)

        return dt_local.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return "n/a"

def _minutes_until(target_iso_local: str) -> Union[int, str]:
    if not target_iso_local or target_iso_local == "n/a":
        return "n/a"
    try:
        s = target_iso_local.strip().replace(" ", "T")
        naive_local = datetime.fromisoformat(s)
        target = naive_local.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        now_local = dt_util.now()
        delta = (target - now_local).total_seconds()
        return int(max(0, round(delta / 60.0)))
    except Exception:
        return "n/a"

def _dig(d: Any, *keys: str, default: Any = None) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _find_first_by_keys(obj: Any, keys: List[str]) -> Optional[Any]:
    stack = [obj]
    keyset = {k for k in keys}
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k in keyset:
                    return v
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None

_PLATFORM_RE = re.compile(r'(?:Platform\s*)(\d+)', re.IGNORECASE)

def _platform_label_from_properties(props: Dict[str, Any]) -> Optional[str]:
    platform_str = props.get('platformName') or props.get('plannedPlatformName') or ''
    if isinstance(platform_str, str) and platform_str.strip():
        m = _PLATFORM_RE.search(platform_str)
        if m:
            return f"Platform {m.group(1)}"
        if 'platform' in platform_str.lower():
            return platform_str.strip()
    return None

def _shorten_label(label: Optional[str]) -> Optional[str]:
    """Return a compact stop label.
    - Keep 'Central Station' exactly.
    - Otherwise, strip everything after the word 'Station'.
    """
    if not label or not isinstance(label, str):
        return None
    s = label.strip()
    if re.match(r"^Central\s+Station\b", s, flags=re.IGNORECASE):
        return "Central Station"
    m = re.match(r"^\s*(.*?)\s+Station\b", s, flags=re.IGNORECASE)
    if m and m.group(1).strip():
        return m.group(1).strip()
    s = re.sub(r",\s*Platform.*$", "", s, flags=re.IGNORECASE)
    s = s.split(",", 1)[0].strip()
    return s or None

def _short_stop_from_node(node: Dict[str, Any]) -> Optional[str]:
    for path in [
        ('disassembledName',),
        ('stop', 'disassembledName'),
        ('stopPoint', 'disassembledName'),
        ('point', 'disassembledName'),
        ('name',),
        ('stop', 'name'),
        ('stopPoint', 'name'),
        ('point', 'name'),
    ]:
        val = _dig(node, *path)
        short = _shorten_label(val) if isinstance(val, str) else None
        if short:
            return short
    return None

def _extract_stop_names(leg: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    ss = leg.get('stopSequence') or leg.get('stopsequence') or []
    if isinstance(ss, list):
        for item in ss:
            if isinstance(item, dict):
                n = _short_stop_from_node(item)
                if n:
                    names.append(n)
    return names

def setup_platform(hass, config, add_entities, discovery_info=None):
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
    include_realtime_location = config[CONF_INCLUDE_REALTIME_LOCATION]
    include_alerts = config[CONF_INCLUDE_ALERTS]
    alert_types = config[CONF_ALERT_TYPES]

    sensor_list = []
    alert_type_full = '|'.join(alert_types) if isinstance(alert_types, list) else str(alert_types)

    for trip in range(0, trips_to_create, 1):
        if trips_to_create == 1:
            name_suffix = ""
        else:
            name_suffix = "_trip_" + str(trip + 1)
        data = PublicTransportData(
            origin_id, destination_id, api_key,
            trip_wait_time, return_info, transport_type,
            strict_transport_type, route_filter,
            include_realtime_location, include_alerts, alert_type_full, trip
        )
        sensor_list.append(TransportNSWv2Sensor(data, name + name_suffix, trip, return_info))

    add_entities(sensor_list, True)

class TransportNSWv2Sensor(Entity):
    def __init__(self, data, name, index, return_info):
        self.data = data
        self._name = name
        self._times = None
        self._return_info = return_info
        self._index = index
        self._state = None
        self._icon = ICONS[None]

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        if self._times is None:
            return {}

        attrTemp = {
            ATTR_DUE_IN: self._times.get(ATTR_DUE_IN),
            ATTR_ARRIVAL_TIME: self._times.get(ATTR_ARRIVAL_TIME),
            ATTR_CHANGES: self._times.get(ATTR_CHANGES),
        }

        if self._return_info in ('medium', 'verbose'):
            attrTemp.update(
                {
                    ATTR_ORIGIN_NAME: self._times.get(ATTR_ORIGIN_NAME),
                    ATTR_ORIGIN_DETAIL: self._times.get(ATTR_ORIGIN_DETAIL),
                    ATTR_DEPARTURE_TIME: self._times.get(ATTR_DEPARTURE_TIME),
                    ATTR_DESTINATION_NAME: self._times.get(ATTR_DESTINATION_NAME),
                    ATTR_DESTINATION_DETAIL: self._times.get(ATTR_DESTINATION_DETAIL),
                    ATTR_OCCUPANCY: self._times.get(ATTR_OCCUPANCY),
                }
            )

        if self._return_info == 'verbose':
            attrTemp.update(
                {
                    ATTR_ORIGIN_LINE_NAME: self._times.get(ATTR_ORIGIN_LINE_NAME),
                    ATTR_ORIGIN_LINE_NAME_SHORT: self._times.get(ATTR_ORIGIN_LINE_NAME_SHORT),
                    ATTR_ORIGIN_TRANSPORT_TYPE: self._times.get(ATTR_ORIGIN_TRANSPORT_TYPE),
                    ATTR_ORIGIN_TRANSPORT_NAME: self._times.get(ATTR_ORIGIN_TRANSPORT_NAME),
                    ATTR_REAL_TIME_TRIP_ID: self._times.get(ATTR_REAL_TIME_TRIP_ID),
                    # Append new fields at the end
                    ATTR_DEPARTURE_TIME_PLANNED: self._times.get(ATTR_DEPARTURE_TIME_PLANNED),
                    ATTR_DEPARTURE_TIME_ESTIMATED: self._times.get(ATTR_DEPARTURE_TIME_ESTIMATED),
                    ATTR_STOP_SEQUENCE: self._times.get(ATTR_STOP_SEQUENCE),
                    ATTR_NUMBER_OF_CARS: self._times.get(ATTR_NUMBER_OF_CARS),
                }
            )

        attrTemp[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attrTemp

    @property
    def unit_of_measurement(self):
        return UnitOfTime.MINUTES

    @property
    def icon(self):
        return self._icon

    def update(self):
        self.data.update()
        self._times = self.data.info
        self._state = self._times.get(ATTR_DUE_IN)
        self._icon = ICONS.get(self._times.get(ATTR_ORIGIN_TRANSPORT_TYPE), ICONS[None])

class PublicTransportData:
    def __init__(
        self,
        origin_id,
        destination_id,
        api_key,
        trip_wait_time,
        return_info,
        transport_type,
        strict_transport_type,
        route_filter,
        include_realtime_location,
        include_alerts,
        alert_type_full,
        index,
    ):
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
            # New defaults
            ATTR_DEPARTURE_TIME_PLANNED: "n/a",
            ATTR_DEPARTURE_TIME_ESTIMATED: "n/a",
            ATTR_STOP_SEQUENCE: [],
            ATTR_NUMBER_OF_CARS: "n/a",
        }
        self.tnsw = TransportNSWv2()

    def update(self):
        try:
            raw = self.tnsw.get_trip(
                name_origin=self._origin_id,
                name_destination=self._destination_id,
                api_key=self._api_key,
                journey_wait_time=self._trip_wait_time,
                transport_type=self._transport_type,
                strict_transport_type=self._strict_transport_type,
                route_filter=self._route_filter,
                journeys_to_return=6,
                raw_output=True,
            )
            if isinstance(raw, str):
                data = json.loads(raw)
            else:
                data = raw

            journeys = data.get('journeys') or []
            if not isinstance(journeys, list) or not journeys:
                _LOGGER.warning("No journeys returned in raw Trip Planner response")
                return

            idx = min(self._index, max(0, len(journeys) - 1))
            j = journeys[idx]

            legs = j.get('legs') or []
            if not legs:
                _LOGGER.warning("Journey has no legs; cannot parse")
                return
            leg0 = legs[0]
            last_leg = legs[-1]

            # ---- Times
            dep_est = (
                _dig(leg0, 'origin', 'departureTimeEstimated')
                or _dig(leg0, 'origin', 'depTimeEstimated')
                or _dig(leg0, 'departureTimeEstimated')
                or _find_first_by_keys(leg0, ['departureTimeEstimated', 'depTimeEstimated'])
            )
            dep_planned = (
                _dig(leg0, 'origin', 'departureTimePlanned')
                or _dig(leg0, 'origin', 'depTimePlanned')
                or _dig(leg0, 'departureTimePlanned')
                or _find_first_by_keys(leg0, ['departureTimePlanned', 'depTimePlanned'])
            )

            arr_est = (
                _dig(last_leg, 'destination', 'arrivalTimeEstimated')
                or _dig(last_leg, 'destination', 'arrTimeEstimated')
                or _dig(last_leg, 'arrivalTimeEstimated')
                or _find_first_by_keys(last_leg, ['arrivalTimeEstimated', 'arrTimeEstimated'])
            )
            arr_planned = (
                _dig(last_leg, 'destination', 'arrivalTimePlanned')
                or _dig(last_leg, 'destination', 'arrTimePlanned')
                or _dig(last_leg, 'arrivalTimePlanned')
                or _find_first_by_keys(last_leg, ['arrivalTimePlanned', 'arrTimePlanned'])
            )

            dep_est_local = _to_local_iso_naive(dep_est)
            dep_planned_local = _to_local_iso_naive(dep_planned)
            arr_local = _to_local_iso_naive(arr_est or arr_planned)

            chosen_dep_local = dep_est_local if dep_est_local != "n/a" else dep_planned_local
            self.info[ATTR_DEPARTURE_TIME] = chosen_dep_local
            self.info[ATTR_DEPARTURE_TIME_ESTIMATED] = dep_est_local
            self.info[ATTR_DEPARTURE_TIME_PLANNED] = dep_planned_local
            self.info[ATTR_ARRIVAL_TIME] = arr_local
            self.info[ATTR_DUE_IN] = _minutes_until(chosen_dep_local)

            # ---- Names / details (short form + platform)
            origin = leg0.get('origin') or {}
            dest = last_leg.get('destination') or {}

            o_short = _short_stop_from_node(origin)
            d_short = _short_stop_from_node(dest)
            self.info[ATTR_ORIGIN_NAME] = o_short or "n/a"
            self.info[ATTR_DESTINATION_NAME] = d_short or "n/a"

            o_props = origin.get('properties') or {}
            d_props = dest.get('properties') or {}
            o_plat = _platform_label_from_properties(o_props)
            d_plat = _platform_label_from_properties(d_props)
            self.info[ATTR_ORIGIN_DETAIL] = o_plat or "n/a"
            self.info[ATTR_DESTINATION_DETAIL] = d_plat or "n/a"

            # Stop IDs if present
            self.info[ATTR_ORIGIN_STOP_ID] = _dig(origin, 'stopId') or _dig(origin, 'id') or "n/a"
            self.info[ATTR_DESTINATION_STOP_ID] = _dig(dest, 'stopId') or _dig(dest, 'id') or "n/a"

            # ---- Transport / line info
            trans = leg0.get('transportation') or {}
            t_type = trans.get('category') or trans.get('product', {}).get('class') or trans.get('product', {}).get('name') or "n/a"
            if isinstance(t_type, int):
                t_type_map = {1: "Train", 5: "Ferry", 7: "Bus", 9: "Light rail", 11: "Metro"}
                t_type = t_type_map.get(t_type, "n/a")
            self.info[ATTR_ORIGIN_TRANSPORT_TYPE] = t_type

            self.info[ATTR_ORIGIN_TRANSPORT_NAME] = trans.get('name') or trans.get('product', {}).get('name') or "n/a"

            # Line long/short
            dest_via = _dig(trans, 'destination', 'name') or "n/a"
            self.info[ATTR_ORIGIN_LINE_NAME] = dest_via
            short_code = trans.get('disassembledName') or trans.get('short_name') or trans.get('product', {}).get('short_name') or trans.get('number') or trans.get('code')
            if not short_code and isinstance(self.info[ATTR_ORIGIN_TRANSPORT_NAME], str):
                parts = self.info[ATTR_ORIGIN_TRANSPORT_NAME].split()
                short_code = parts[0] if parts and len(parts[0]) <= 3 else None
            self.info[ATTR_ORIGIN_LINE_NAME_SHORT] = short_code or "n/a"

            # ---- Occupancy if present
            occ = leg0.get('occupancy') or j.get('occupancy') or _find_first_by_keys(leg0, ['occupancy', 'crowding'])
            self.info[ATTR_OCCUPANCY] = occ if isinstance(occ, (str, int, float)) else ("n/a" if occ is None else str(occ))

            # ---- Changes (transfers)
            changes = j.get('changes')
            if not isinstance(changes, int):
                changes = max(0, len(legs) - 1)
            self.info[ATTR_CHANGES] = changes

            # ---- realtime trip id if present
            rtid = j.get('realtimeTripId') or leg0.get('realtimeTripId') or _find_first_by_keys(j, ['realtimeTripId', 'realTimeTripId', 'rtTripId'])
            self.info[ATTR_REAL_TIME_TRIP_ID] = rtid or "n/a"

            # ---- New fields
            self.info[ATTR_STOP_SEQUENCE] = _extract_stop_names(leg0)

            # number_of_cars
            num_cars = (
                j.get('NumberOfCars') or
                _dig(j, 'properties', 'NumberOfCars') or
                _dig(origin, 'properties', 'NumberOfCars') or
                _dig(trans, 'properties', 'numberOfCars') or
                trans.get('numberOfCars')
            )
            self.info[ATTR_NUMBER_OF_CARS] = num_cars if num_cars is not None else "n/a"

        except Exception as err:
            _LOGGER.error("TransportNSW raw trip fetch failed: %s", err)
            return
