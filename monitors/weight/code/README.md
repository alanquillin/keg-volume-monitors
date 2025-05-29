# Weight Based Keg Volume Monitor: Controller Firmware

## Setting up wifi

To initiate or update the WiFi for a given device, make sure to add your wifi redencials to the local `wifi-creds.json`.  

``` json
{
    "network": "MYSSID",
    "security": "WPA2_PSK",
    "password": "MYWIFIPASS",
    "hidden": false
}
```

for more details see the [documentation](https://docs.particle.io/reference/developer-tools/cli/).

Then update the device with following command

``` shell
make initi-wifi
```
