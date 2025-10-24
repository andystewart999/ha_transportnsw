# Transport NSW MkII
A Home Assistant custom component to provide real-time Transport NSW journey information

## History
This integration was initially inspired by Home Assistant's built-in [Transport NSW](https://www.home-assistant.io/integrations/transport_nsw/) integration but has now been completely re-written from scratch to incorporate a GUI-based setup and Home Assistant's recent addition of [Config Subentries](https://developers.home-assistant.io/blog/2025/02/16/config-subentries/).  It uses my modified version of the TransportNSW library that can be found on PyPi [here](https://pypi.org/project/PyTransportNSWv2/), and can be installed via [HACS](https://github.com/hacs/integration).

## Use
You need a Transport NSW API key, available for free [here](https://opendata.transport.nsw.gov.au/data/user/register) - once registered, create an API token.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/63c24e05-3b32-4065-9d00-77855e233a62" />


### Add the config entry
From the devices page, click 'Add integration', search for 'Transport NSW Mk II' and add it.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/f1de7f72-5512-446f-8d25-7464f6f050d3" />

Enter the API token and how often you want the sensors to update and you're done!  At this stage there's only one sensor which logs how many API calls the integration has made across all subentries.  There's a limit of 60,000 calls per day and each journey, on average, requires 3 API calls - in the unlikely event that you're going to run out a future enhancement may be to auto-throttle sensor updates.

<img width="500" alt="API key entry" src="https://raw.githubusercontent.com/andystewart999/ha_transportnsw/d95f7eae1929cf81124896b35a40884193ca584f/images/1%20-%20config%20entry.png" />



### Journey subentries
Each journey is a subentry and has its own journey-specific set of options.  Journey-specific options can be chosen at the time of creation or at any time afterwards.  Each config flow page has a detailed explanation of the options it provides, including filtering based on your preferred transport types (train, bus, etc).



### Origin and destination
You can specify the origin and destination either by stop ID or the full name of the location.  If you enter the full (or partial) name, for example 'Central Station', the `stop_finder` API call will be called and whatever comes back as the 'best' (as determined by the API) will be used.  Using known stop IDs are obviously less likely to result in the integration choosing the wrong location, but in most cases you'll get what you want the first time.

<img width="500" alt="Journey subentry" src="https://raw.githubusercontent.com/andystewart999/ha_transportnsw/refs/heads/master/images/2%20-%20subentry%20origin%20and%20destination%20%28populated%29.png" />



### Journey filters
On a per-journey basis you can specify the transport type options that are applicable, and, to give you time to get to the origin, how far in the future a journey departure time must be to be considered valid.

<img width="500" alt="Journey filters" src="https://raw.githubusercontent.com/andystewart999/ha_transportnsw/refs/heads/master/images/3%20-%20subentry%20filters.png" />



### Multiple trips
Up to 3 trips per journey can be created, which are basically the next 3 departures from the origin.  Note that depending on your 'transport type' choices the trips may be quite different, and may also have some duplicated legs - it's entirely up to the Transport NSW API what to return.

<img width="500" alt="Alerts and multiple trips" src="https://raw.githubusercontent.com/andystewart999/ha_transportnsw/refs/heads/master/images/4%20-%20subentry%20alerts%20and%20trips.png" />



### Default sensors
To keep things simple the default sensors comprise only of the 'due' sensor, showing minutes until departure time, and device tracker sensors for the origin and destination vehicles (assuming the API returns that information).


### Additional sensors
There are many additional sensors that are available if required, which can be selected when you create a new journey or at any time afterwards.  Origin/destination names, exact stops or platforms, the number of changes, the vehicle type - pretty much everything that the API returns can be included.

<img width="500" alt="Additional sensors" src=https://raw.githubusercontent.com/andystewart999/ha_transportnsw/refs/heads/master/images/6%20-%20subentry%20sensor%20detail.png />



### Attributes 
Some of the sensors have their own additional attributes:

- Changes: The state of this sensor is the number of changes within the journey.  The attributes are a pipe-separate list of each platform that you'll traverse as part of the journey.  It doesn't include the origin or destination platforms as they're available as individual sensors.
- Alerts: The state of this sensor is the highest alert returned by the API.  The attributes are the full JSON dump of the alert details, which can be processed by your automations or template sensors as required
- Device tracker: The API real-time trip ID is included for your reference.
