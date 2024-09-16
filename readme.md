
### WeeWX extension to broadcast WeatherFlow UDP API compliant UDP JSON messages

This extension emits UDP to the specified port as defined in the WeatherFlow UDP API
ref: https://weatherflow.github.io/Tempest/api/udp/v171/

The initial intent is to support running the excellent WeatherFlow PiConsole app
to display a dashboard versus any weewx capable weather station.

### Installation

To install, use the weewx extension installer with the appropriate syntax
for your version of weewx.  This installs a default set of configurations
that 'must' be edited to match your system.

See the [broadcastWeatherFlowUDP] section in weewx for details, but a short
description of what is needed follows.

1. Edit your udpIP port to match the broadcast address for your weewx system.
   Unfortunately this might differ based on your weewx platform os and version.

2. Edit the sensor_map if needed.  For each element you want to map the key
   to the weewx field you want to use for data.

3. Restart weewx to see it take effect.

You can verify it works interactively by running 'weewxd' normally in a terminal
setting, following the instructions for your weewx version and installation method.

### Notes:

 * the WeatherFlow PiConsole is available from https://github.com/peted-davis/WeatherFlow_PiConsole
   with its forums at https://community.tempest.earth/t/weatherflow-piconsole/20083

 * the WeatherFlow PiConsole as delivered by its author assumes you have set it
   up per his instructions. A sample wfpiconsole.ini using US units is here for reference.

   You likely want to edit your TempestHeight (meters), Lat/Lon, Timezone, and Name
   so that you get the correct time and weather forecast for your location.

   The CheckWX key (top of file) and setting rest_api=1 (bottom of file) is needed
   for forecasts to work.  Ensure Connection=UDP (bottom of file) so the wfpiconsole
   listens for the UDP broadcasts from the weewx system using this extension.  At this
   time you need a WeatherFlow API key (sorry) for the forecast to actually work.

   Simplest way to proceed is to install the wfpiconsole and copy this example .ini
   into place as /home/pi/wfpiconsole/wfpiconsole.ini and edit lightly as indicated
   above.  Then run "wfpiconsole start" and you should see the console come up and
   display data in a few seconds.

 * the PiConsole has some limitations when you run in UDP mode.  These are not bugs
   so please do not complain to me nor to Peter.  In general these limitations are
   due to differences in how the WeatherFlow APIs sometimes require an actual station
   for things like trend data.
