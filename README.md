# ha-transportnsw
A Home Assistant component to provide real-time Transport NSW journey information

##
This is a custom fork of Home Assistant's built-in Transport NSW integration.  It uses a modified version of the TransportNSW library that can be found on PyPi here: https://pypi.org/project/PyTransportNSWv2/

Unlike the built-in integration, the specific origin and destination are specified rather than the origin and a general route.  Both general stop IDs (such as stations or bus stops) can be specified, as well as more stop IDs such as specific platforms.  As this isn't specifically a route-showing service, for longer journeys that involve a number of changes or multiple journey types only the origin, final destination and the number of changes are shown.

One of the key requests features for the built-in version was the option to specificy a minimum 'wait time' to give people the time to get to the origin.  This is now an option, although the side-effect is that as soon as a train, for example, gets _too_ close to the station it will disappear and the sensor will jump to the next further away train. 

The detail of the returned information can be selected, from brief through to verbose (see the later examples).  All detail iterations include the latitude and longitude (if the TransportNSW API returns it) so the current location of the vehicle can be shown on a map.

### Example settings
```yaml
sensor:
  - platform: transport_nsw
    name: 'Pymble to Central'
    origin_id: 10101122
    destination_id: 10101100
    trip_wait_time: 15
    return_info: verbose
    api_key: 'your_api_key'
```

### All settings explained
* name - the name of the sensor.  The default is 'Next Journey'.
* origin_id: the Transport NSW platform or stop ID of the origin.
* destination_id: the Transport NSW platform or stop ID of the destination.
* trip_wait_time: the minimum time from now until the journey should start, in minutes.  The default is 0.
* return_info: defines the level of detail that the sensor should include.  Valid options are basic, medium and verbose - the default is medium.
* api_key: your Transport NSW API key

### Example sensors

```yaml
return_info: basic
```

asdasdasd

```yaml
return_info: medium
```

asdasdasd

```yaml
return_info: verbose
```

asdasdasd


