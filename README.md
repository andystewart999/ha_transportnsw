# ha-transportnsw
A Home Assistant custom component to provide real-time Transport NSW journey information

##
This is a fork of Home Assistant's built-in Transport NSW integration.  It uses my modified version of the TransportNSW library that can be found on PyPi here: https://pypi.org/project/PyTransportNSWv2/

Unlike the built-in integration, the specific origin and destination are specified rather than the origin and a general route.  Both general stop IDs (such as stations or bus stops) can be specified, as well as more detailed stop IDs such as specific platforms.  As this isn't specifically a detailed route display service, for longer journeys that involve a number of changes or multiple journey types only the origin, final destination and the number of changes are shown.
 
One of the most often requested feature additions for the built-in version was the option to specificy a minimum 'wait time' to give people the time to get to the origin.  This is now an option, although the side-effect is that as soon as a train, for example, gets _too_ close to the station it will disappear and the sensor will jump to the next further away train. 

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

Walking segments that top or tail the returned journey are ignored.  For example, if you specifiy an origin that requires you to walk to the nearest bus stop, that bus stop is considered to be the origin rather than wherever your defined `origin_id` is.

```yaml
return_info: basic
```
<img src="https://github.com/andystewart999/ha-transportnsw/blob/master/images/basic_sensor.JPG" width=250>
<br> 

```yaml
return_info: medium
```
<img src="https://github.com/andystewart999/ha-transportnsw/blob/master/images/medium_sensor.JPG" width=250>
<br> 

```yaml
return_info: verbose
```
<img src="https://github.com/andystewart999/ha-transportnsw/blob/master/images/verbose_sensor.JPG" width=250>
<br> 

### Future enhancements
To manage the disappearance of journeys that are too close in time (if `trip_wait_time` is set), I'd like to enable the creation of 'child' sensors for all journeys that have been previously returned, have not yet left the origin but are closer in time than the minimum.  These child sensors would probably only show the arrival time and the latitude and longitude so they can be shown on a map as that's probably the only real value.
