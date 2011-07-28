#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2011 Sasu Karttunen <sasu.karttunen@tpnet.fi>
#
#    This file is part of D-Bus Python Weather API Service (pywapi-dbus).
#
#    pywapi-dbus is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pywapi-dbus is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pywapi-dbus.  If not, see <http://www.gnu.org/licenses/>.

# About information
__author__=("Sasu Karttunen")
__email__=("sasu.karttunen@tpnet.fi")
__version__=("0.1-git")
__website__=("https://github.com/skfin/pywapi-dbus")

# Import dbus service and mainloop-glib. Needed to run a dbus service. 
try:
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gobject import MainLoop
except:
    print ("You don't seem to have required dbus Python libraries.")
    exit(1)

# Import pywapi. We use modified version of it so we want to import it from pywapidbus package rather than the original pywapi even if it's already installed.
try:
    import pywapidbus.pywapi 
except:
    print ("Oops, you have no Python Weather API. Though, pywapi-dbus should ship it. If you think it is our fault, contact us.")
    exit(1)

# Return codes! Integer numbers are easier for client program to handle since pywapi-dbus is ment to be used as backend.
errSuccess = int(0) # not really an error :)
errUnregisteredSender = int(100)
errPywapiError = int(101)
errInvalidLocation = int(102)
errUnknownUnit = int(103)
errIncorrectDayID = int(104)


class GoogleAPI(dbus.service.Object):
    # Initializing our dbus service 
    def __init__(self):
        busName = dbus.service.BusName('org.pywapi.Daemon', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/GoogleAPI')
        self.clients = {} # We use sender parameter in order to let multiple apps use this service at same time
        self.bus = dbus.SessionBus()

        
    def checkIndex(self, sender):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        
    def checkDay(self, day):
        if day < 3:
            return errIncorrectDayID
        
    # Set current location and retrieve the weather information. Replies with integer 0 for success, 1 for failure.
    # It's faster to retrieve weather now rather than every time temperature, condition or etc. is requested.
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'ss', sender_keyword = 'sender')
    def setLocation(self, location, locale, sender=None):
        try:
            self.clients[sender] = pywapidbus.pywapi.get_weather_from_google(location, locale)
        except:
            return errPywapiError
        try: # Checks if the location is valid. Just checking if city exists, could be something else, no specific reason.
            self.clients[sender]['forecast_information']['city']
        except:
            del self.clients[sender] # Delete reference to incorrect location :)
            return errInvalidLocation
        def clearDict(new_owner):
            if new_owner == '': # Sender disconnected from D-Bus, clearing information
                del self.clients[sender]
        self.bus.watch_name_owner(sender, clearDict)
        return errSuccess
    
    # Let the client be nice to us and say that it's done it's busines and don't need us anymore :)
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def clear(self, sender):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        del self.clients[sender]
        return errSuccess
    
    # Replies with a current city name and area (state, province or something like that)
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def city(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecast_information']['city']
    
    # Replies with a current location's postal code (or city name if non-US city, I guess...)
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def postalCode(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecast_information']['postal_code']
    
    # Replies with a forecast's generation date (format: YYYY-MM-DD)
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def forecastDate(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecast_information']['forecast_date']
    
    # Replies with a server date and time
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def currentDateTime(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecast_information']['current_date_time']
    
    # Replies with currently used unit system. Used in forecasts.
    # This value is based on locale used in gSetLocation. Doesn't affect gCurrentTemperature though.
    @dbus.service.method('org.pywapi.Daemon')
    def unitSystem(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecast_information']['unit_system']
    
    # Replies with a current condition of location (Cloudy or etc.).
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def currentCondition(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['current_conditions']['condition']
    
    # Replies with a current temperature of location in Celsius or Fahrenheits
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def currentTemperature(self, units, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if units == "metric":
            return self.clients[sender]['current_conditions']['temp_c']
        elif units == "imperial":
            return self.clients[sender]['current_conditions']['temp_f']
        else:
            return errUnknownUnit

    # Replies with a current air humidity. The output kind of sucks, but it's not our problem 8)
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def currentHumidity(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['current_conditions']['humidity']
    
    # Replies with a Google icon of current weather condition (but why? is a good question).
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def currentIcon(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['current_conditions']['icon']
    
    # Replies with a current wind condition. The result kind of sucks (again) but it's Google, not us!
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def currentWindCondition(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['current_conditions']['wind_condition']
    
    # These functions take day number as attribute. 0 is today, 1 is tomorrow and so on.
    # Replies with a day of week (short format)
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastDayOfWeek(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['day_of_week']
    
    # Replies with a condition in forecast (not current condition!).
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastCondition(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['condition']
    
    # Replies with a max (highest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMax(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['high']
    
    # Replies with a min (lowest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMin(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['high']
    
    # Replies with a forecast condition icon (from Google)
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastIcon(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['icon']
 

    @dbus.service.method('org.pywapi.Daemon')
    def countryList(self):
        return pywapidbus.pywapi.get_countries_from_google()
    
    # Replies a list of cities in country
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's')
    def cityList(self, country):
        return pywapidbus.pywapi.get_cities_from_google(country)
    
class YahooAPI(dbus.service.Object):
    # Initializing our dbus service 
    def __init__(self):
        busName = dbus.service.BusName('org.pywapi.Daemon', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/YahooAPI')
        self.clients = {}
        self.bus = dbus.SessionBus()
        
    def checkIndex(self, sender):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        
    def checkDay(self, day):
        if day > 1:
            return errIncorrectDayID
 
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'ss', sender_keyword = 'sender')
    def setLocation(self, location_id, units, sender=None):
        try:
            self.clients[sender] = pywapidbus.pywapi.get_weather_from_yahoo(location_id, units)
        except IndexError: # Pywapi gives this when given an invalid location
            return errInvalidLocation
        except:
            return errPywapiError
        def clearDict(new_owner):
            if new_owner == '': # Sender disconnected from D-Bus, clearing information
                del self.clients[sender]
                watch.cancel() # Do not watch the client anymore since it has disconnected
        # Watches the unique bus name and calls clearDict() when it's owner changes (most likely client disconnects from session bus)
        watch =  self.bus.watch_name_owner(sender, clearDict)
        return errSuccess   
    
    def clear(self, sender):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        del self.clients[sender]
        return errSuccess
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def link(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['link']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def locationCity(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']['city']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def locationRegion(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']['region']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def locationCountry(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']['country']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def geoLatitude(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['geo']['lat']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def geoLongitude(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['geo']['long']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def unitsDistance(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['units']['distance']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def unitsPressure(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['units']['pressure']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def unitsSpeed(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['units']['speed']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def unitsTemperature(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['units']['temperature']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def astronomySunrise(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['astronomy']['sunrise']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def astronomySunset(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['astronomy']['sunset']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def atmosphereHumidity(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['atmosphere']['humidity']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def atmospherePressure(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['atmosphere']['pressure']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def atmosphereRising(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['atmosphere']['rising']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def atmosphereVisibility(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['atmosphere']['visibility']
    
    @dbus.service.method('org.pywapi.Daemon', out_signature = 'i', sender_keyword = 'sender')
    def conditionCode(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['condition']['code']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def conditionDate(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['condition']['date']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def conditionTemperature(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['condition']['temp']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def conditionText(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['condition']['text']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def conditionTitle(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['condition']['title']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', out_signature = 'i', sender_keyword = 'sender')
    def forecastCode(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['code']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windChill(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind']['chill']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windDirection(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind']['direction']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windSpeed(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind']['speed']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastDate(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['date']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMax(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['high']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMin(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['low']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastText(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if self.checkDay(day) == 104:
            return errIncorrectDayID
        return self.clients[sender]['forecasts'][day]['text']

class NoaaAPI(dbus.service.Object):
    def __init__(self):
        busName = dbus.service.BusName('org.pywapi.Daemon', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/NoaaAPI')
        self.clients = {}
        self.bus = dbus.SessionBus()
              
    def checkIndex(self, sender):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def setLocation(self, location_id, sender=None):
        try:
            self.clients[sender] = pywapidbus.pywapi.get_weather_from_noaa(location_id) # This fails on incorrect location so we dont need to delete the key :P
        except:
            return errInvalidLocation
        def clearDict(new_owner):
            if new_owner == '':
                del self.clients[sender]
        self.bus.watch_name_owner(sender, clearDict)
        return errSuccess
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def clear(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        del self.clients[sender]
        return errSuccess
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def dewpoint(self, units, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if units == 'metric':
            return self.clients[sender]['dewpoint_c']
        elif units == 'imperial':
            return self.clients[sender]['dewpoint_f']
        else:
            return errUnknownUnit
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def dewpointString(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['dewpoint_string']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def heatIndex(self, units, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if units == 'metric':
            return self.clients[sender]['heat_index_c']
        elif units == 'imperial':
            return self.clients[sender]['heat_index_f']
        else:
            return errUnknownUnit
        
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def heatIndexString(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['heat_index_string']
        
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def iconUrl(self, sender=None): #Nah, lets just append these, I'm getting lazy
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['icon_url_base'] + self.clients[sender]['icon_url_name']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def latitude(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['latitude']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def longitude(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['longitude']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def location(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def observationURL(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['ob_url']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def observationTime(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['observation_time']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def observationTimeRFC822(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['observation_time_rfc822']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def pressure(self, unit, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if unit == 'mbar':
            return self.clients[sender]['pressure_mb']
        elif unit == 'inhg':
            return self.clients[sender]['pressure_in'] # Who the hell uses inch of mercury as air pressure unit?!?
        else:
            return errUnknownUnit
        
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def pressureString(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['pressure_string']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def relativeHumidity(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['relative_humidity']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def stationID(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['station_id']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def suggestedPickup(self, sender=None): # ?!?!
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['suggested_pickup']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def suggestedPickupPeriod(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['suggested_pickup_period']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def temperature(self, units, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if units == 'metric':
            return self.clients[sender]['temp_c']
        elif units == 'imperial':
            return self.clients[sender]['temp_f']
        else:
            return errUnknownUnit
        
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def temperatureString(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['temperature_string']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def twoDayHistoryURL(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['two_day_history_url']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def condition(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['weather']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windDegrees(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind_degrees']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windDir(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind_dir']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windGustMPH(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind_gust_mph']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windMPH(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind_mph']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def windString(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['wind_string']
    
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def windchill(self, units, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        if units == 'metric':
            return self.clients[sender]['windchill_c']
        elif units == 'imperial':
            return self.clients[sender]['windchill_f']
        else:
            return errUnknownUnit
        
    @dbus.service.method('org.pywapi.Daemon', in_signature = 's', sender_keyword = 'sender')
    def windchillString(self, units, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['windchill_string']
    
class Application(dbus.service.Object): # Some methods about ourselves
    def __init__(self):
        busName = dbus.service.BusName('org.pywapi.Daemon', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/App')
        
    @dbus.service.method('org.pywapi.Daemon')
    def version(self):
        return __version__
    
    @dbus.service.method('org.pywapi.Daemon')
    def author(self):
        return __author__
    
    @dbus.service.method('org.pywapi.Daemon')
    def email(self):
        return __email__
    
    @dbus.service.method('org.pywapi.Daemon')
    def website(self):
        return __website__
    
    @dbus.service.signal('org.pywapi.Daemon')
    def ready(self): # Send a signal that service is ready to receive calls
        pass
    
class Main():
    # Run the loop and classes
    DBusGMainLoop(set_as_default = True)
    g=GoogleAPI();y=YahooAPI();n=NoaaAPI();a=Application()
    a.ready()
    mainloop = MainLoop()
    mainloop.run()
