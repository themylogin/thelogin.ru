#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime as _datetime, timedelta

def russian_month(date_string):
    return date_string.replace("January",      u"января").\
                       replace("February",     u"февраля").\
                       replace("March",        u"марта").\
                       replace("April",        u"апреля").\
                       replace("May",          u"мая").\
                       replace("June",         u"июня").\
                       replace("July",         u"июля").\
                       replace("August",       u"августа").\
                       replace("September",    u"сентября").\
                       replace("October",      u"октября").\
                       replace("November",     u"ноября").\
                       replace("December",     u"декабря")

def format_date(datetime, format="%e %B %Y"):
    return russian_month(datetime.strftime(format))

def format_time(datetime, format="%H:%M"):
    return datetime.strftime("%H:%M")

def format_datetime(datetime, date_format="%e %B %Y", time_format="%H:%M"):
    return format_date(datetime, date_format) + ", " + format_time(datetime, time_format)

def format_datetime_relative(datetime, relative_to=None):
    if relative_to == None:
        relative_to = _datetime.now()

    if datetime.date() == relative_to.date():
        return format_time(datetime)
    else:
        if datetime.date() == relative_to.date() - timedelta(days=1):
            return u"Вчера, " + format_time(datetime)
        else:
            if datetime.year == relative_to.year:
                return format_datetime(datetime, date_format="%e %B")
            else:
                return format_datetime(datetime)

def format_date_period(datetime1, datetime2):
    if datetime1.year != datetime2.year:
        return format_date(datetime1) + " - " + format_date(datetime2)
    else:
        if datetime1.month != datetime2.month:
            return format_date(datetime1, "%e %B") + " - " + format_date(datetime2)
        else:
            return format_date(datetime1, "%e") + " - " + format_date(datetime2)
