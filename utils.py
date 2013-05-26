#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib

"""
Metaclass for objects with read-only properties. E.g.:
class Config:
    __metaclass__ = ReadonlyPropertiesMetaclass
    __readonly__ = {
        "property1" : "value1",
        "property2" : "value2"
    }
"""
class ReadonlyPropertiesMetaclass(type):
    def __new__(cls, classname, bases, classdict):
        def readonly_getter_factory(attrname):
            def getter(self):
                return self.__readonly__[attrname]

            return getter

        readonly = classdict.get("__readonly__", {})
        for name,default in readonly.items():
            classdict[name] = property(readonly_getter_factory(name))

        return type.__new__(cls, classname, bases, classdict)

# PHP-style
def ucfirst(s):
    return s[0].upper() + s[1:]

def urlencode(s):
    return urllib.quote(s.encode("utf-8"), "")

def urlencode_plus(s):
    return urllib.quote_plus(s.encode("utf-8"), "")
