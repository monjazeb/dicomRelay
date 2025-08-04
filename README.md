## simple DICOM Relay
This program implements a forwarding DICOM relay which redirects every C-STORE request to a new destination.

You can configure relay and destination in `config.json`

```json
{
    "relay": {
        "ip": "127.0.0.1",
        "ae_title": "RELAY",
        "port": 11112
    },
    "forward": {
        "ip": "127.0.0.1",
        "ae_title": "DESTINATION",
        "port": 11113
    },
    "debug": true,
    "anonymize": true
}
```
A log is created as `dicom.log` if `debug` is `true`.

There is no exit key. You must kill it or restart!

for further qustions ask me at [My Email](mailto:armonj@gmail.com) or find me on [GitHub](https://github.com/monjazeb)

