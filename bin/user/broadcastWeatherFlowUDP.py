
'''
#
# This extension emits UDP to the specified port as defined in the WeatherFlow UDP API
# ref: https://weatherflow.github.io/Tempest/api/udp/v171/
#
# The intent is to be able to use any app that consumes that UDP broadcast
# expecially the excellent WeatherFlow Pi Console available on github at
#
#
#-------------------------------------------------------------------------
# To manually install, add this extension to report_services
#    report_services = ...,user.broadcastWeatherFlowUDP.BroadcastWeatherFlowUDP
#
# Add the following [broadcastWeatherFlowUDP] stanza to weeex.conf and edit to taste.
#
# The [[sensor_map]] maps expected WeatherFlow UDP API data elements to weewx 
# archive REC elements. If you do not have any of the wind/rain/solar/temp
# sensors set the applicable elements to None here.
#
# This example is for an Ecowitt station with a WS85 wind/rain sensor
# as well as an outside temperature/sensor
#-------------------------------------------------------------------------
#
# [broadcastWeatherFlowUDP]
#     devSN = ST-00006021      # anything here will work 
#     hubSN = HB-12345678      # anything here will work
#     udpPort = 50222          # typical WeatherFlow UDP port
#     udpIP = 192.168.1.255    # broadcast address for the pi subnet
#                              # or 255.255.255.255
#                              # or 0.0.0.0
#
#     [[sensor_map]]
#       wind_lull                     = None                 # no real weewx element for this
#       wind_avg                      = windSpeed
#       wind_gust                     = windGust
#       wind_direction                = windGustDir          # or windDir if so inclined to use that
#       wind_sample_interval          = interval             # for ecowitt = gw1000 driver poll_interval
#       station_pressure              = pressure
#       air_temperature               = outTemp
#       relative_humidity             = outHumidity
#       illuminance                   = None                 # uncertain what weewx value is
#       uv                            = UV                   # should be UV typically
#       solar_radiation               = None                 # should be radiation typically
#       rain_accumulated              = dayRain              # weewx rain = rain in this period, not dayRain
#       precipitation_type            = None                 # see api
#       lightning_strike_avg_distance = None                 # see api
#       lightning_strike_count        = None                 # see api
#       battery                       = windBatteryStatus
#       report_interval               = interval             # for ecowitt = poll_interval * 2 (?)
# 
#-------------------------------------------------------------------------
#
# example observation and UDP emitted by the WeatherFlow Hub for reference here
#
#        serial_number = data["serial_number"]
#        obs_st["obs"][0][0] = now          #                           seconds_since_epoch
#        obs_st["obs"][0][1] = null         # wind_lull                 meters/second min 3 sec sample
#        obs_st["obs"][0][2] = windSpeed    # wind_ave                  meters/second avg over report interval
#        obs_st["obs"][0][3] = windGust     # wind_gust                 meters_second max 3 sec sample
#        obs_st["obs"][0][4] = windDir      # wind_direction            degrees 
#        obs_st["obs"][0][5] = null         # wind_sample_interval      seconds
#        obs_st["obs"][0][6] = pressure     # station_pressure          MB
#        obs_st["obs"][0][7] = outTemp      # air_temperature           deg-C
#        obs_st["obs"][0][8] = outHumidity  # relative_humidity         %
#        obs_st["obs"][0][9] = null         # illuminance               lux
#        obs_st["obs"][0][10] = null        # uv                        index
#        obs_st["obs"][0][11] = null        # solar_radiation           W/m^2
#        obs_st["obs"][0][12] = rain        # rain_accumulated          mm (in this reporting interval)
#        obs_st["obs"][0][13] = null        # precipitation_type        0=none, 1=rain, 2=hail
#        obs_st["obs"][0][14] = null        # lightning_strike_distance km
#        obs_st["obs"][0][15] = null        # lightning_strike_count    count
#        obs_st["obs"][0][16] = lull        # battery                   volts
#        obs_st["obs"][0][17] = interval    # report_interval           minutes
#        obs_st["firmware_revision"] = null
#
#        {
#                "serial_number": "ST-00000512",
#                "type": "obs_st",
#                "hub_sn": "HB-00013030",
#                "obs": [
#                    [1588948614,0.18,0.22,0.27,144,6,1017.57,22.37,50.26,328,0.03,3,0.000000,0,0,0,2.410,1]
#                ],
#                "firmware_revision": 129
#        }

'''

from weewx.engine import StdPrint
from weeutil.weeutil import timestamp_to_string
import weewx.units

import json
import socket
import sys

data   = { }
fields = { } 

class BroadcastWeatherFlowUDP(StdPrint):

    def __init__(self, engine, config_dict):
        super().__init__(engine, config_dict)

        # these are the expected WeatherFlow obs_st data elements, skipping time_epoch which is always weewx dateTime
        fields['obs_st'] = ('wind_lull', 'wind_avg', 'wind_gust', 'wind_direction', 'wind_sample_interval', 
                            'station_pressure', 'air_temperature', 'relative_humidity', 'illuminance', 'uv', 
                            'solar_radiation', 'rain_accumulated', 'precipitation_type', 'lightning_strike_avg_distance', 
                            'lightning_strike_count', 'battery', 'report_interval')

# not necessary any more....
#
#        # we check the sensor_map for completion here
#        for item in fields['obs_st']:
#            try:
#                i = config_dict['broadcastWeatherFlowUDP']['sensor_map'][item]
#            except:
#                # debug only
#                print("===> sensor_map is missing", item)
#
##                # somehow this doesn't work below
#                config_dict['broadcastWeatherFlowUDP']['sensor_map'][item] = None

        self.devSN   = config_dict['broadcastWeatherFlowUDP']['devSN']
        self.hubSN   = config_dict['broadcastWeatherFlowUDP']['hubSN']
        self.udpPort = config_dict['broadcastWeatherFlowUDP']['udpPort']
        self.udpIP   = config_dict['broadcastWeatherFlowUDP']['udpIP']

    '''
       this comes from the LOOP data so it's a "packet"
    '''
    def process_rapid_wind(self,event):

        packet_wx = weewx.units.to_METRICWX(event.packet)

        epoch     = packet_wx['dateTime']
        direction = packet_wx.get('windGustDir',0)
        gust      = packet_wx.get('windSpeed')

        # ref:  https://weatherflow.github.io/Tempest/api/udp/v171/
        #                                                                                      [epoch, mps, degrees]
        # { "serial_number": "SK-00008453", "type":"rapid_wind", "hub_sn": "HB-00000001", "ob":[1493322445,2.3,128] }

        data['serial_number'] = self.devSN
        data['type']          = "rapid_wind"
        data['hub_sn']        = self.hubSN

        try:
            direction = round(direction)
            if direction == 360:
                direction = 0
        except:
            direction = 0

        data['ob']            = [ epoch, gust, direction ]

        myjson = json.dumps(data)

        # TODO: only if debug=2
        print(); print("MYWIND    : ", myjson); print()

        self.broadcastWeatherFlowUDP(myjson)
        
    '''
       this comes from the ARCHIVE data so it's an "event"
    '''
    def process_obs_st(self,event):
        # TODO: only if debug=2
        print("OBS_ST\n")

        record_wx = weewx.units.to_METRICWX(event.record)

        epoch = record_wx['dateTime']

        # ecowitt REC record contents for our station...
        #
        # {'dateTime': 1725909100, 'inTemp': 21.4, 'outTemp': 18.199999999999996, 'inHumidity': 59.0, 'outHumidity': 80.0, 'pressure': 1003.3999999999999, 'relbarometer': 1003.3999999999999, 'extraTemp1': 21.599999999999998, 'extraTemp2': 22.399999999999995, 'extraTemp3': 22.1, 'extraTemp4': 21.4, 'extraTemp5': 19.8, 'extraHumid1': 62.0, 'extraHumid2': 56.0, 'extraHumid3': 59.0, 'extraHumid4': 64.0, 'extraHumid5': 72.0, 'soilTemp1': 19.099999999999998, 'soilMoist1': 26.0, 'rain': None, 'stormRain': 0.0, 'rainRate': 0.0, 'dayRain': 0.0, 'weekRain': 0.0, 'monthRain': 0.10000000000000002, 'yearRain': 0.10000000000000002, 'windSpeed': 0.6000014912945679, 'windDir': 63.0, 'windGust': 0.6000014912945679, 'windGustDir': 63.0, 'daymaxwind': 1.6000039767855145, 'wh32_batt': 0.0, 'wh31_ch1_batt': 0, 'wh31_ch2_batt': 0, 'wh31_ch3_batt': 0, 'wh31_ch4_batt': 0, 'wh31_ch5_batt': 0, 'wn34_ch1_batt': 1.5, 'wh51_ch1_batt': 1.4, 'wh32_sig': 4.0, 'wh31_ch1_sig': 4, 'wh31_ch2_sig': 4, 'wh31_ch3_sig': 4, 'wh31_ch4_sig': 4, 'wh31_ch5_sig': 4, 'wn34_ch1_sig': 4, 'wh51_ch1_sig': 4, 'ws85_sig': 4, 'windBatteryStatus': 3.08, 'altimeter': 1003.4901125904614, 'appTemp': 19.28452668158725, 'barometer': 1003.3999999999999, 'cloudbase': 437.76155304613303, 'dewpoint': 14.689217663981031, 'ET': None, 'heatindex': 18.16444444444444, 'humidex': 21.98439011430788, 'inDewpoint': 13.049402739927952, 'maxSolarRad': 0.0, 'windchill': 18.199999999999996, 'windrun': 0.00600001491294568, 'interval': 0.16666666666666666, 'usUnits': 17}

        obs_st = { }
        obs_st['serial_number']     = self.devSN
        obs_st['hub_sn']            = self.hubSN
        obs_st['serial_number']     = data['serial_number']
        obs_st['type']              = "obs_st"
        obs_st['firmware_revision'] = None                      # not in the weewx REC record

        # TODO: only if debug=2
        print(record_wx)

#        fields['obs_st'] = ('wind_lull', 'wind_avg', 'wind_gust', 'wind_direction', 'wind_sample_interval', 
#                            'station_pressure', 'air_temperature', 'relative_humidity', 'illuminance', 'uv', 
#                            'solar_radiation', 'rain_accumulated', 'precipitation_type', 'lightning_strike_avg_distance', 
#                            'lightning_strike_count', 'battery', 'report_interval')

        sensor_map = self.config_dict['broadcastWeatherFlowUDP']['sensor_map']
        keys = sensor_map.keys()

        # unfortunately we need a try/except block for each expected obs_st element
        # to catch where the sensor_map maps it to None or to an element not present
        # in the observed REC record from weewx

        try:
            wind_lull = record_wx[sensor_map['wind_lull']]
        except:
            wind_lull = None
        try:
            wind_avg = record_wx[sensor_map['wind_avg']]
        except:
            wind_avg = None
        try:
            wind_gust = record_wx[sensor_map['wind_gust']]
        except:
            wind_gust = None
        try:
            wind_direction = record_wx[sensor_map['wind_direction']]
        except:
            wind_direction = None
        try:
            wind_sample_interval = record_wx[sensor_map['wind_sample_interval']]
        except:
            wind_sample_interval = None
        try:
            station_pressure = record_wx[sensor_map['station_pressure']]
        except:
            station_pressure = None
        try:
            air_temperature = record_wx[sensor_map['air_temperature']]
        except:
            air_temperature = None
        try:
            relative_humidity = record_wx[sensor_map['relative_humidity']]
        except:
            relative_humidity = None
        try:
            illuminance = record_wx[sensor_map['illuminance']]
        except:
            illuminance = None
        try:
            uv = record_wx[sensor_map['uv']]
        except:
            uv = None
        try:
            solar_radiation = record_wx[sensor_map['solar_radiation']]
        except:
            solar_radiation = None
        try:
            rain_accumulated = record_wx[sensor_map['rain_accumulated']]
        except:
            rain_accumulated = None
        try:
            precipitation_type = record_wx[sensor_map['precipitation_type']]
        except:
            precipitation_type = None
        try:
            lightning_strike_avg_distance = record_wx[sensor_map['lightning_strike_avg_distance']]
        except:
            lightning_strike_avg_distance = None
        try:
            lightning_strike_count = record_wx[sensor_map['lightning_strike_count']]
        except:
            lightning_strike_count = None
        try:
            battery = record_wx[sensor_map['battery']]
        except:
            battery = 0    ### wfpiconsole wants a number here
        try:
            report_interval = record_wx[sensor_map['report_interval']]
        except:
            report_interval = None

        obs_st['obs'] = [ [
                           record_wx['dateTime'],
                           wind_lull,
                           wind_avg,
                           wind_gust, 
                           wind_direction, 
                           wind_sample_interval,
                           station_pressure, 
                           air_temperature, 
                           relative_humidity, 
                           illuminance, 
                           uv,
                           solar_radiation,
                           rain_accumulated,
                           precipitation_type,
                           lightning_strike_avg_distance,
                           lightning_strike_count,
                           battery,
                           report_interval
                        ] ]

        myjson = json.dumps(obs_st)

        # TODO: only if debug=2
        print(); print("MYTEMPEST : ", myjson); print()

        self.broadcastWeatherFlowUDP(myjson)

        # debug only
        # sys.exit(1)

    def new_loop_packet(self,event):
        # TODO: only if debug=2
        print("-------------------------")
        self.process_rapid_wind(event)

    def new_archive_record(self,event):
        # TODO: only if debug=2
        print("-------------------------")
        print("\nMYARCHIVE\n")
        self.process_obs_st(event)

    def broadcastWeatherFlowUDP(self,message):
        # TODO: only if debug=2
        print("\nBROADCAST_UDP\n")
        sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto( str.encode(message), (self.udpIP, int(self.udpPort)) )
        sock.close()

#-----------------------------------------------------------
