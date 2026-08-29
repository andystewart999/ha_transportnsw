# Transport NSW MkII
[![Last release version](https://img.shields.io/github/v/release/andystewart999/ha_transportnsw)](https://github.com/andystewart999/ha_transportnsw/releases)
[![Last release date](https://img.shields.io/github/release-date/andystewart999/ha_transportnsw)](https://github.com/andystewart999/ha_transportnsw/releases)
[![Contributors](https://img.shields.io/github/contributors/andystewart999/ha_transportnsw)](https://github.com/andystewart999/ha_transportnsw/graphs/contributors)
[![Project license](https://img.shields.io/github/license/andystewart999/ha_transportnsw)](https://github.com/andystewart999/ha_transportnsw/blob/master/LICENSE)
![hacs](https://img.shields.io/badge/hacs-standard_installation-darkorange.svg)
![type](https://img.shields.io/badge/type-custom_component-forestgreen.svg)



A Home Assistant custom component to provide real-time Transport NSW journey information

## History
This integration was initially inspired by Home Assistant's built-in [Transport NSW](https://www.home-assistant.io/integrations/transport_nsw/) integration but has now been completely re-written from scratch to incorporate a GUI-based setup and Home Assistant's recent addition of [Config Subentries](https://developers.home-assistant.io/blog/2025/02/16/config-subentries/).  It uses my modified version of the TransportNSW library that can be found on PyPi [here](https://pypi.org/project/PyTransportNSWv2/), and can be installed via [HACS](https://github.com/hacs/integration).

## Use
You need a Transport NSW API key, available for free [here](https://opendata.transport.nsw.gov.au/data/user/register) - once registered, create an API token.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/0_apikey.png)

### Add the config entry
From the devices page, click 'Add integration', search for 'Transport NSW Mk II' and add it.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/0_newintegration.png)

Enter the API token and how often you want the sensors to update and you're done!  At this level there's only one sensor that logs how many API calls the integration has made across all subentries.  There's a limit of 60,000 calls per day and each journey, on average, requires 3 API calls - in the unlikely event that you're going to run out a future enhancement may be to auto-throttle sensor updates.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/1_configentry.png)

### Journey subentries
Each journey is a [subentry](https://developers.home-assistant.io/docs/config_entries_index#config-subentries) and has its own journey-specific set of options.  Journey-specific options can be chosen at the time of creation or at any time afterwards.  Each config flow page has a detailed explanation of the options it provides, including filtering based on your preferred transport types (train, bus, etc).

### Origin and destination
You can specify the origin and destination(s) either by stop ID or the full name of the location.  If you enter the full (or partial) name, for example 'Central Station', the `stop_finder` API call will be called and whatever comes back as the 'best' (as determined by the API) will be used.  Using known stop IDs are obviously less likely to result in the integration choosing the wrong location, but in most cases you'll get what you want the first time.

If you provide multiple destinations for a journey you will get the earliest journey that stops at _any_ of them.  You can also select a Device Tracker as the origin, which obviously means that the origin will change as you move around.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/2b_subentryoriginanddestination.png)

### Journey filters - transport types
On a per-journey basis you can specify the transport type options that you want to include, for both the first and last legs.. for journeys without a change the last leg is obviously also the first leg and still needs appropriate filters settings.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/3_subentryfilters.png)

### Journey filters - changes and run/route filters
To give you time to get to the origin you can specify how far in the future a journey departure time must be to be considered valid.  You can also filter how many changes you're willing to make, and finally there's an optional text filter on the full and short line name (e.g 'T1 North Shore & Western Line', '195').

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/3b_subentryfilters.png)

### Multiple trips
Up to 3 trips per journey can be created, which are basically the next 3 departures from the origin sorted by the arrival time at the destination.  Note that depending on your 'transport type' choices the trips may be quite different, and may also have some duplicated legs - it's entirely up to the Transport NSW API what to return.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/4_subentryalertsandtrips.png)

This is where you can also specify if the journey should only be updated between two periods.  This allows you to potentially reduce your daily API usage quite significantly, with the knock-on benefit that the integration can update more regularly.

### Default sensors
To keep things simple the default sensors comprise only of the 'due' sensor, showing minutes until departure time.  If the origin is itself a device tracker a device tracker sensor showing the location of the first leg is also shown by default.  There are many other sensors that you can select... if you intend to use the Lovelace card you need to make sure that you at least include ```first/last leg occupancy detail```.

### Alerts
You can choose to include an alerts sensor based on various filters.  If the journey has any alerts that meet your filter, the highest alert is shown.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/5_subentryalertdetail.png)

### Additional sensors
There are many additional sensors that are available if required, which can be selected when you create a new journey or at any time afterwards.  Origin/destination names, exact stops or platforms, the number of changes, the vehicle type - pretty much everything that the API returns can be included.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/6b_subentrysensordetail.png)

### Attributes 
Some of the sensors have their own additional attributes:

- Changes: The state of this sensor is the number of changes within the journey.  The ```stops``` attribute contains a simple comma-separated list of origin, destination and stations where there is a change.  The ```detailed stops``` attribute is a dictlist that includes every relevant (origin, changes, destination) stop on the journey, plus the locations of the first leg and last leg vehicles (if available).
- Occupancy:  The state of this sensor is the general vehicle occupancy level, if available.  The ```occupancy detail``` attribute contains a dictlist of per-carriage occupancy detail, if available.
- Occupancy detail:  The state of this sensor is a glyph-based representation of the per-carriage occupancy, if available.  The ```occupancy detail``` attribute contains the same information as the Occupancy sensor's ```occupancy detail``` attribute.
- Alerts: The state of this sensor is the highest alert returned by the API.  The attributes are the full JSON dump of the alert details, which can be processed by your automations or template sensors as required.
- Device tracker: The stop name and ID are included.

## Automatic update interval
At the config entry level you can set the update interval in the traditional fashion, or set it to `automatic`.  The integration maintains a rolling average of how many API calls are used at each poll - when on automatic that information, along with how many API calls are left from the daily allocation and how far through the day it is, to determine an appropriate update interval.  If new journeys are created or removed they will be catered for automatically.

![Alt text of the image](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/1_config_entry_options.png)

When running on `automatic` you can tell the integration how much of the daily allocation it's allowed to use... this can be helpful if you're using the same API key in multiple Home Assistant deployments, where each deployment can be allowed to consume, for example, 48% of the daily allowance.

## Lovelace card
A custom Lovelace card is included for your dashboards.  It shows per-carriage detailed occupancy in the same style as the Transport NSW train information boards, and scales automatically depending on the length of the vehicle and the number of carriages or equivalent that it has.  As well as showing occupancy detail you can optionally select one or more sensor states to show in the top-right corner of the card, rotating through each one at a rate of your choosing:

![Custom Lovelace card](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/www/vehicle-occupancy-card.png)

The card fully supports Home Assistant's section view, has a graphical editor and will also be offered as a suggestion in the 'by entity' picker:

![Card suggestion](https://github.com/andystewart999/ha_integration_resources/blob/main/documentation/ha_transportnsw/www/card-suggestions.png)


