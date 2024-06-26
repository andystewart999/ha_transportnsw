# ha_transportnsw
A Home Assistant custom component to provide real-time Transport NSW journey information

##
This is a fork of Home Assistant's built-in Transport NSW integration.  It uses my modified version of the TransportNSW library that can be found on PyPi here: https://pypi.org/project/PyTransportNSWv2/

Unlike the built-in integration, the specific origin and destination are specified rather than the origin and a general route.  Both general stop IDs (such as stations or bus stops) can be specified, as well as more detailed stop IDs such as specific platforms.  As this isn't specifically a detailed route display service, for longer journeys that involve a number of changes or multiple journey types only the origin, final destination and the number of changes are shown for clarity.
 
One of the most often requested feature additions for the built-in version was the option to specify a minimum 'wait time' to give people the time to get to the origin.  This is now an option, although the side-effect is that as soon as a train, for example, gets _too_ close to the station it will disappear and the sensor will jump to the next further away train.

Another feature is the ability to filter by transport type, for example Train.  You can specify if the filter should be strict, in which case the first leg of the journey has to be of the specified type, or not strict in which case a journey will be returned if _any_ of the legs are of the specified type.

Finally, you can specify how many trips should be returned and therefore how many sensors for that particular journey should be created.  Note that the TransportNSW API only ever returns 5 or 6 trips, so specifying a strict filter might result in less sensors being generated than requested.  Trips are returned by the departure time from the specified origin and could of course be via different routes or transport types, depending on your origin, destination and filter settings.

The detail of the returned information can be selected, from brief through to verbose (see the examples below).  All detail iterations include the latitude and longitude (if the TransportNSW API returns it) so the current location of the vehicle can be shown on a map.

### Example settings
```yaml
sensor:
  - platform: ha_transportnsw
    api_key: 'your_api_key'
    origin_id: 206710
    destination_id: 207210
    trip_wait_time: 5
    transport_type: 1 # Only trains
    return_info: medium
    strict_transport_type: true
    trips_to_create: 3
    name: "Chatswood to Gordon"
```

### All settings explained
* name - the name of the sensor.  The default is 'Next Journey'.
* origin_id: the Transport NSW platform or Stop ID of the origin.
* destination_id: the Transport NSW platform or Stop ID of the destination.
* trip_wait_time: the minimum time from now until the journey should start, in minutes.  The default is 0.
* transport_type: a transport type, as defined by the TransportNSW API, that must be present in a journey for it to be returned by the API.  The default is no filter.
* return_info: defines the level of detail that the sensor should include.  Valid options are basic, medium and verbose - the default is medium.
* api_key: your Transport NSW API key

### transport_type filters
```
1: Train
4: Light rail
5: Bus
7: Coach
9: Ferry
11: School bus
99: Walk
100: Walk
107: Cycle
```
Walking segments that top or tail the returned journey are ignored.  For example, if you specifiy an origin that requires you to walk to the nearest bus stop, that bus stop is considered to be the origin rather than wherever your defined `origin_id` is.

### return_info examples
```yaml
return_info: basic
```
<img width="500" alt="basic" src="https://github.com/andystewart999/ha_transportnsw/assets/18434441/3cb11d26-d029-4250-bac6-19df8480e9ef">

```yaml
return_info: medium
```
<img width="500" alt="medium" src="https://github.com/andystewart999/ha_transportnsw/assets/18434441/eab2f2c3-1c4d-416a-80c5-15410c3d8fc4">

```yaml
return_info: verbose
```
<img width="500" alt="verbose" src="https://github.com/andystewart999/ha_transportnsw/assets/18434441/f2a95957-bbeb-41f8-aa9b-7efee8e62452">

