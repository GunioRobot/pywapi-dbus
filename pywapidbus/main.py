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

""" This is application provides a dbus service that lets other
applications receive weather information through dbus.The main goal
is to provide same functionality as Python Weather API (pywapi) but
as an daemon that provides information through dbus so that many apps can use it.
Useful or not? Who knows. (: """

from PyQt4.QtCore import QCoreApplication

# Import dbus service and mainloop-glib. Needed to run a dbus service.
try:
    import dbus.service
    from dbus.mainloop.qt import DBusQtMainLoop
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
        return self.clients[sender]['forecasts'][day]['day_of_week']
    
    # Replies with a condition in forecast (not current condition!).
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastCondition(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecasts'][day]['condition']
    
    # Replies with a max (highest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMax(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecasts'][day]['high']
    
    # Replies with a min (lowest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMin(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['forecasts'][day]['high']
    
    # Replies with a forecast condition icon (from Google)
    @dbus.service.method('org.pywapi.Daemon', in_signature = 'i', sender_keyword = 'sender')
    def forecastIcon(self, day, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
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
        self.bus.watch_name_owner(sender, clearDict)
        return errSuccess   
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def title(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['title']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def link(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['link']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def htmlDescription(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['html_description']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def city(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']['city']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def region(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']['region']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def country(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['location']['country']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def latitude(self, sender=None):
        if self.checkIndex(sender) == 100:
            return errUnregisteredSender
        return self.clients[sender]['geo']['lat']
    
    @dbus.service.method('org.pywapi.Daemon', sender_keyword = 'sender')
    def longnitude(self, sender=None):
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
    
    @dbus.service.method('org.pywapi.Daemon')
    def doMemoryDump(self):
        from meliae import scanner
        scanner.dump_all_objects("/home/skfin/Development/meliae.dump")
    
    
    
class Main():
    DBusQtMainLoop(set_as_default = True)
    app = QCoreApplication([])
    g=GoogleAPI();y=YahooAPI();
    app.exec_()
