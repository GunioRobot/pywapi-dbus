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
    print "It seems that you don't have required PyQt4's QtCore module installed."
    exit(1)

# Import dbus service and mainloop-qt. Needed to run a dbus service.
try:
    import dbus.service
    from dbus.mainloop.qt import DBusQtMainLoop
except:
    print "You don't seem to have required dbus Python libraries."
    exit(1)

# Import pywapi. Since pywapi is not very common library to systems have, we provide it with pywapi-dbus. It's licensed under MIT license.
try:
    import pywapi
except:
    print "Oops, you have no Python Weather API. Though, pywapi-dbus should ship it. If you think it is our fault, contact us."
    exit(1)

# Return codes! Integer numbers are easier for client program to handle since pywapi-dbus is ment to be used as backend.
errSuccess = int(0) # not really an error :)
errNoLocation = int(100)
errPywapiError = int(101)
errInvalidLocation = int(102)
errUnknownUnit = int(103)
errIncorrectDayID = int(104)

class Main(dbus.service.Object):
    # Initializing our dbus service 
    def __init__(self):
        busName = dbus.service.BusName('org.pywapi.Weather', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/GoogleAPI')
 
    # GOOGLE PART STARTS HERE !!! (functions prefixed with g)
    # Set current location and retrieve the weather information. Replies with integer 0 for success, 1 for failure.
    # It's faster to retrieve weather now rather than every time temperature, condition or etc. is requested.
    @dbus.service.method('org.pywapi.Weather', in_signature = 'ss')
    def gSetLocation(self, location, locale):
        try:
            self.google_pywapi = pywapi.get_weather_from_google(location, locale)
        except:
            return errPywapiError
        try: # Checks if the location is valid. Just checking if city exists, could be something else, no specific reason.
            self.google_pywapi['forecast_information']['city']
        except:
            del self.google_pywapi # Delete reference to incorrect location :)
            return errInvalidLocation
        return errSuccess
    
    # Replies with a current city name and area (state, province or something like that)
    @dbus.service.method('org.pywapi.Weather')
    def gCity(self):
        try: # This thing here checks if location is set.
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        City = self.google_pywapi['forecast_information']['city']
        return City
    
    # Replies with a current location's postal code (or city name if non-US city, I guess...)
    @dbus.service.method('org.pywapi.Weather')
    def gPostalCode(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        PostalCode = self.google_pywapi['forecast_information']['postal_code']
        return PostalCode
    
    # Replies with a forecast's generation date (format: YYYY-MM-DD)
    @dbus.service.method('org.pywapi.Weather')
    def gForecastDate(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        forecastDate = self.google_pywapi['forecast_information']['forecast_date']
        return forecastDate
    
    # Replies with a server date and time
    @dbus.service.method('org.pywapi.Weather')
    def gCurrentDateTime(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        currentDateTime = self.google_pywapi['forecast_information']['current_date_time']
        return currentDateTime
    
    # Replies with currently used unit system. Used in forecasts.
    # This value is based on locale used in gSetLocation. Doesn't affect gCurrentTemperature though.
    @dbus.service.method('org.pywapi.Weather')
    def gUnitSystem(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        unitSystem = self.google_pywapi['forecast_information']['unit_system']
        return unitSystem
    
    # Replies with a current condition of location (Cloudy or etc.).
    @dbus.service.method('org.pywapi.Weather')
    def gCurrentCondition(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        currentCondition = self.google_pywapi['current_conditions']['condition']
        return currentCondition
    
    # Replies with a current temperature of location in Celsius or Fahrenheits
    @dbus.service.method('org.pywapi.Weather', in_signature = 's')
    def gCurrentTemperature(self, units):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        if units == "metric":
            currentTemperature = self.google_pywapi['current_conditions']['temp_c']
        elif units == "imperial":
            currentTemperature = self.google_pywapi['current_conditions']['temp_f']
        else:
            return errUnknownUnit
        return currentTemperature

    # Replies with a current air humidity. The output kind of sucks, but it's not our problem 8)
    @dbus.service.method('org.pywapi.Weather')
    def gCurrentHumidity(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        currentHumidity = self.google_pywapi['current_conditions']['humidity']
        return currentHumidity
    
    # Replies with a Google icon of current weather condition (but why? is a good question).
    @dbus.service.method('org.pywapi.Weather')
    def gCurrentIcon(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        currentIcon = self.google_pywapi['current_conditions']['icon']
        return currentIcon
    
    # Replies with a current wind condition. The result kind of sucks (again) but it's Google, not us!
    @dbus.service.method('org.pywapi.Weather')
    def gCurrentWindCondition(self):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        currentWindCondition = self.google_pywapi['current_conditions']['wind_condition']
        return currentWindCondition
    
    # These functions take day number as attribute. 0 is today, 1 is tomorrow and so on.
    # Replies with a day of week (short format)
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i')
    def gForecastDayOfWeek(self, day):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        if day > int(3):
            return errIncorrectDayID
        forecastDayOfWeek = self.google_pywapi['forecasts'][day]['day_of_week']
        return forecastDayOfWeek
    
    # Replies with a condition in forecast (not current condition!).
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i')
    def gForecastCondition(self, day):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        forecastTodayCondition = self.google_pywapi['forecasts'][day]['condition']
        return forecastTodayCondition
    
    # Replies with a max (highest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i')
    def gForecastTMax(self, day):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        forecastTMax = self.google_pywapi['forecasts'][day]['high']
        return forecastTMax
    
    # Replies with a min (lowest) temperature. Uses default unit set by locale!
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i')
    def gForecastTMin(self, day):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        forecastTMin = self.google_pywapi['forecasts'][day]['high']
        return forecastTMin
    
    # Replies with a forecast condition icon (from Google)
    @dbus.service.method('org.pywapi.Weather', in_signature = 'i')
    def gForecastIcon(self, day):
        try:
            self.google_pywapi
        except AttributeError:
            return errNoLocation
        forecastIcon = self.google_pywapi['forecasts'][day]['icon']
        return forecastIcon

    @dbus.service.method('org.pywapi.Weather')
    def gCountrylist(self):
        googleCountries = pywapi.get_countries_from_google()
        return googleCountries
    
    # Replies a list of cities in country
    @dbus.service.method('org.pywapi.Weather', in_signature = 's')
    def gCityList(self, country):
        googleCities = pywapi.get_cities_from_google(country)
        return googleCities
          
DBusQtMainLoop(set_as_default = True)
app = QCoreApplication([])
main = Main()
app.exec_()