#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import dateutil.parser
import simplejson
import urllib2

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        username,
        session_id, card_number,
        
        item_cases      = (u"поездка",  u"поездки", u"поездке",     u"поездку", u"поездкой",    u"поездке"),
        item_mcases     = (u"поездки",  u"поездок", u"поездкам",    u"поездки", u"поездками",   u"поездках"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.username = username

        self.session_id = session_id
        self.card_number = card_number

    def get_provider(self):
        return Provider(self.session_id, self.card_number)

    def get_formatter(self):
        return Formatter(self.username)

    def get_editor(self):
        return None

class Provider(abstract.Provider):
    def __init__(self, session_id, card_number):
        self.session_id = session_id
        self.card_number = card_number

    def provide(self):
        opener = urllib2.build_opener()
        opener.addheaders.append(("Cookie", "ASP.NET_SessionId=%(session_id)s; tcard_ek_pan=%(card_number)s" % {
            "session_id"    : self.session_id,
            "card_number"   : self.card_number,
        }))
        trips_history = simplejson.loads(opener.open("https://t-karta.ru/ek/SitePages/TransportServicePage.aspx?functionName=GetCardTripsHistory&pan=%(pan)s&dateFrom=%(dateFrom)s&dateTo=%(dateTo)s" % {
            "pan"           : self.card_number,
            "dateFrom"      : (datetime.datetime.now() - datetime.timedelta(days=13)).strftime("%d.%m.%Y"),
            "dateTo"        : datetime.datetime.now().strftime("%d.%m.%Y"),
        }).read())["TripsHistory"]
        if trips_history:
            for trip in trips_history:
                yield self.provider_item(
                    id          =   trip["Time"],
                    created_at  =   dateutil.parser.parse(trip["Time"], dayfirst=True),
                    data        =   trip,
                    kv          =   {}
                )

class Formatter(abstract.Formatter):
    def __init__(self, username):
        self.username = username

    def get_title(self, content_item):
        return """<b>%(username)s</b> """ % {
            "username"  : self.username,
        } + {
            u"метро"            : lambda: u"зашёл в метро на станции «" + {
                "MARKS"             : u"Площадь Маркса",
                "STUD"              : u"Студенческая",
                "RECHV"             : u"Речной вокзал",
                "OKT"               : u"Октябрьская",
                "LENIN"             : u"Площадь Ленина",
                "KR-PR"             : u"Красный проспект",
                "GAGAR"             : u"Гагаринская",
                "ZAELC"             : u"Заельцовская",

                "G-M"               : u"Площадь Гарина-Михайловского",
                "POKR"              : u"Маршала Покрышкина",
                "BEREZ"             : u"Берёзовая роща",
                "NIVA"              : u"Золотая Нива",
            }[content_item.data["RouteNum"]] + u"»",

            u"мун. автобус"     : lambda: u"ехал на автобусе №" + content_item.data["RouteNum"],
            u"мун. трамвай"     : lambda: u"ехал на трамвае №" + content_item.data["RouteNum"],
            u"мун. троллейбус"  : lambda: u"ехал на троллейбусе №" + content_item.data["RouteNum"],
            u"ком. автобус"     : lambda: u"ехал на автобусе №" + content_item.data["RouteNum"],
        }[content_item.data["RouteType"]]()

    def get_image(self, content_item):
        return "/asset/img/content/type/tcard_trip/" + content_item.data["RouteType"] + "/48.png"

    def get_description(self, content_item, url):
        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {}
