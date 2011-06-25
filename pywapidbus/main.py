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

# Importing QCoreApplication from QtCore. Needed for DBusQtMainLoop.
try:
    from PyQt4.QtCore import QCoreApplication
except:
    print ("It seems that you don't have required PyQt4's QtCore module installed.")
    exit(1)

# Import dbus service and mainloop-qt. Needed to run a dbus service.
try:
    import dbus.service
    from dbus.mainloop.qt import DBusQtMainLoop
except:
    print ("You don't seem to have required dbus Python libraries.")
    exit(1)

# Import pywapi. Since pywapi is not very common library to systems have, we provide it with pywapi-dbus. It's licensed under MIT license.
try:
    import pywapi
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

class Main(dbus.service.Object):
    # Initializing our dbus service 
    def __init__(self):
        busName = dbus.service.BusName('org.pywapi.Weather', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/GoogleAPI')
        self.clients = {} # We use sender parameter in order to let multiple apps use this service at same time
 
    # GOOGLE PART STARTS HERE !!! (functions prefixed with g)
    # Set current location and retrieve the weather information. Replies with integer 0 for success, 1 for failure.
    # It's faster to retrieve weather now rather than every time temperature, condition or etc. is requested.
    @dbus.service.method('org.pywapi.Weather', in_signature = 'ss', sender_keyword = 'sender')
    def setLocation(self, location, locale, sender=None):
        try:
            self.clients[sender] = pywapi.get_weather_from_google(location, locale)
        except:
            return errPywapiError
        try: # Checks if the location is valid. Just checking if city exists, could be something else, no specific reason.
            self.clients[sender]['forecast_information']['city']
        except:
            del self.clients[sender] # Delete reference to incorrect location :)
            return errInvalidLocation
        print sender
        return errSuccess
    
    # Replies with a current city name and area (state, province or something like that)
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def city(self, sender=None):
        try: # This thing here checks if location is set.
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        City = self.clients[sender]['forecast_information']['city']
        return City
    
    # Replies with a current location's postal code (or city name if non-US city, I guess...)
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def postalCode(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        PostalCode = self.clients[sender]['forecast_information']['postal_code']
        return PostalCode
    
    # Replies with a forecast's generation date (format: YYYY-MM-DD)
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def forecastDate(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        forecastDate = self.clients[sender]['forecast_information']['forecast_date']
        return forecastDate
    
    # Replies with a server date and time
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def currentDateTime(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        currentDateTime = self.clients[sender]['forecast_information']['current_date_time']
        return currentDateTime
    
    # Replies with currently used unit system. Used in forecasts.
    # This value is based on locale used in gSetLocation. Doesn't affect gCurrentTemperature though.
    @dbus.service.method('org.pywapi.Weather')
    def unitSystem(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        unitSystem = self.clients[sender]['forecast_information']['unit_system']
        return unitSystem
    
    # Replies with a current condition of location (Cloudy or etc.).
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def currentCondition(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        currentCondition = self.clients[sender]['current_conditions']['condition']
        return currentCondition
    
    # Replies with a current temperature of location in Celsius or Fahrenheits
    @dbus.service.method('org.pywapi.Weather', in_signature = 's', sender_keyword = 'sender')
    def currentTemperature(self, units, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        if units == "metric":
            currentTemperature = self.clients[sender]['current_conditions']['temp_c']
        elif units == "imperial":
            currentTemperature = self.clients[sender]['current_conditions']['temp_f']
        else:
            return errUnknownUnit
        return currentTemperature

    # Replies with a current air humidity. The output kind of sucks, but it's not our problem 8)
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def currentHumidity(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        currentHumidity = self.clients[sender]['current_conditions']['humidity']
        return currentHumidity
    
    # Replies with a Google icon of current weather condition (but why? is a good question).
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def currentIcon(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        currentIcon = self.clients[sender]['current_conditions']['icon']
        return currentIcon
    
    # Replies with a current wind condition. The result kind of sucks (again) but it's Google, not us!
    @dbus.service.method('org.pywapi.Weather', sender_keyword = 'sender')
    def currentWindCondition(self, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        currentWindCondition = self.clients[sender]['current_conditions']['wind_condition']
        return currentWindCondition
    
    # These functions take day number as attribute. 0 is today, 1 is tomorrow and so on.
    # Replies with a day of week (short format)
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i', sender_keyword = 'sender')
    def forecastDayOfWeek(self, day, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        if day > int(3):
            return errIncorrectDayID
        forecastDayOfWeek = self.clients[sender]['forecasts'][day]['day_of_week']
        return forecastDayOfWeek
    
    # Replies with a condition in forecast (not current condition!).
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i', sender_keyword = 'sender')
    def forecastCondition(self, day, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        forecastTodayCondition = self.clients[sender]['forecasts'][day]['condition']
        return forecastTodayCondition
    
    # Replies with a max (highest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMax(self, day, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        forecastTMax = self.clients[sender]['forecasts'][day]['high']
        return forecastTMax
    
    # Replies with a min (lowest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i', sender_keyword = 'sender')
    def forecastTMin(self, day, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        forecastTMin = self.clients[sender]['forecasts'][day]['high']
        return forecastTMin
    
    # Replies with a forecast condition icon (from Google)
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i', sender_keyword = 'sender')
    def forecastIcon(self, day, sender=None):
        try:
            self.clients[sender]
        except KeyError:
            return errUnregisteredSender
        forecastIcon = self.clients[sender]['forecasts'][day]['icon']
        return forecastIcon

    @dbus.service.method('org.pywapi.Weather')
    def countryList(self):
        googleCountries = pywapi.get_countries_from_google()
        return googleCountries
    
    # Replies a list of cities in country
    @dbus.service.method('org.pywapi.Weather', in_signature = 's')
    def cityList(self, country):
        googleCities = pywapi.get_cities_from_google(country)
        return googleCities
          
DBusQtMainLoop(set_as_default = True)
app = QCoreApplication([])
main = Main()
app.exec_()