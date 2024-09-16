# installer for the BroadcastWeatherFlowUDP extension
# Copyright 2024 Vince Skahan <vinceskahan@gmail.com>
# Distributed under the terms of the GNU Public License (GPLv3)

import configobj
from setup import ExtensionInstaller

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

#-------- extension info -----------

VERSION         = "0.1"
NAME            = 'broadcastWeatherFlowUDP'
DESCRIPTION     = 'broadcast UDP compliant with WeatherFlow UDP API'
AUTHOR          = "Vince Skahan"
AUTHOR_EMAIL    = "vinceskahan@gmail.com"
REPORT_SERVICES = 'user.broadcastWeatherFlowUDP.BroadcastWeatherFlowUDP'

#-------- main loader -----------

def loader():
    return BroadcastWeatherFlowUDPInstaller()

class BroadcastWeatherFlowUDPInstaller(ExtensionInstaller):
    def __init__(self):
        super(BroadcastWeatherFlowUDPInstaller, self).__init__(
            version=VERSION,
            name=NAME,
            description=DESCRIPTION,
            author=AUTHOR,
            author_email=AUTHOR_EMAIL,
            report_services=REPORT_SERVICES,
            config=config_dict,
            files=files_dict
        )

#----------------------------------
#         config stanza
#----------------------------------

extension_config = """

#-----------------------------------------------------------
# sensor_map is the order specified in the obs_st
# observation as specified in:
#    https://weatherflow.github.io/Tempest/api/udp/v171/
#
# If you do not have the wind/rain/solar/temp sensor(s)
# set the applicable elements to None here
#
# For the udpIP element below, use the broadcast address
# of the subnet the wfpiconsole pi is on
#
# Note: udpIP = 255.255.255.255 does not seem to work well
#
# see the actual .py code for more details
#-----------------------------------------------------------

[broadcastWeatherFlowUDP]
    devSN = ST-00006021      # anything here will work
    hubSN = HB-12345678      # anything here will work
    udpPort = 50222          # typical WeatherFlow UDP port
    udpIP = 192.168.1.255    # broadcast address for the pi subnet

    # map expected Tempest obs_st data elements to corresponding weewx REC record elements
    [[sensor_map]]
	wind_lull                     = None                 # no real weewx element (?)
	wind_avg                      = windSpeed
	wind_gust                     = windGust
	wind_direction                = windGustDir          # or windDir if so inclined to use that
	wind_sample_interval          = interval             # for ecowitt = poll_interval
	station_pressure              = pressure
	air_temperature               = outTemp
	relative_humidity             = outHumidity
	illuminance                   = None                 # uncertain what weewx value is
	uv                            = UV                   # should be UV typically
	solar_radiation               = None                 # should be radiation typically
	rain_accumulated              = dayRain              # weewx rain = rain in this period, not dayRain
	precipitation_type            = None                 # see api
	lightning_strike_avg_distance = None                 # see api
	lightning_strike_count        = None                 # see api
	battery                       = 1
	report_interval               = 20                   # for ecowitt = 10 ????


"""
config_dict = configobj.ConfigObj(StringIO(extension_config))

#----------------------------------
#        files stanza
#----------------------------------
files=[('bin/user', ['bin/user/broadcastWeatherFlowUDP.py'])]
files_dict = files

#---------------------------------
#          done
#---------------------------------

