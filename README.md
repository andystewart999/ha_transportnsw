# ha-transportnsw
A Home Assistant component to provide real-time Transport NSW journey information

### Parameters
```python
.get_trip(origin_stop_id, destination_stop_id, api_key, [trip_wait_time = 0])
```

### Parameters
```yaml
sensor:
  - platform: transport_nsw
    name: 'Pymble to Central'
    origin_id: 10101122
    destination_id: 10101100
    trip_wait_time: 15
    api_key: 'your_api_key'
```
