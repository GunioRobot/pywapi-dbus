#!/usr/bin/python
# -*- coding: utf-8 -*-
import dbus
 
bus = dbus.SessionBus()
helloservice = bus.get_object('org.pywapi.Weather', '/Weather')
condition = helloservice.get_dbus_method('condition', 'org.pywapi.Weather')
print condition()