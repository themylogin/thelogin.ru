#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        username,
        imap_server, imap_login, imap_password,
        
        item_cases      = (u"транзакция",   u"транзакции",  u"транзакции",  u"транзакцию",  u"транзакцией",     u"транзакции"),
        item_mcases     = (u"транзакции",   u"транзакций",  u"транзакциям", u"транзакции",  u"транзакциеями",   u"транзакциях"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.username = username

        self.imap_server = imap_server
        self.imap_login = imap_login
        self.imap_password = imap_password

    def get_provider(self):
        return Provider(self.imap_server, self.imap_login, self.imap_password)

    def get_formatter(self):
        return Formatter(self.username)

class Provider(abstract.Provider):
    def __init__(self, imap_server, imap_login, imap_password):
        self.imap_server = imap_server
        self.imap_login = imap_login
        self.imap_password = imap_password

    def provide(self):
        import imaplib
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.imap_login, self.imap_password)
        mail.list()
        mail.select("inbox")

        result, data = mail.uid("search", None, "(FROM \"notify@vtb24.ru\")")
        for uid in data[0].split():
            result, data = mail.uid("fetch", uid, "(RFC822)")
            raw_email = data[0][1]

            import re
            data = re.search("([0-9.]+) v ([0-9:]+) po Vashey bankovskoy karte VTB24 .+ proizvedena tranzaktsiya po oplate na summu ([0-9.]+) (.+?)\. .+ Detali platezha: (.+?)\.", raw_email)
            if data:
                import dateutil.parser
                yield self.provider_item(
                    id          =   uid,
                    created_at  =   dateutil.parser.parse(data.group(1) + " " + data.group(2), dayfirst=True),
                    data        =   {
                        "sum"       : float(data.group(3)),
                        "currency"  : data.group(4),
                        "reason"    : "Retail " + data.group(5),
                    },
                    kv          =   {}
                )

class Formatter(abstract.Formatter):
    def __init__(self, username):
        self.username = username

    def get_title(self, content_item):
        return """<b>%(username)s</b> """ % {
            "username"  : self.username,
        } + self.parse_reason(content_item)["title"]

    def get_image(self, content_item):
        return "/asset/img/content/type/vtb24_transaction/48.png"

    def get_description(self, content_item, url):
        reason = self.parse_reason(content_item)
        if "location" in reason:
            return '<a href="http://maps.yandex.ru/?ll=%(ll)s&amp;pt=%(ll)s,pm2rdl&amp;l=map&amp;size=640,240&amp;z=14" style="display: block; background: url(http://static-maps.yandex.ru/1.x/?ll=%(ll)s&amp;pt=%(ll)s,pm2rdl&amp;l=map&amp;size=640,280&amp;z=14) center no-repeat; width: 100%%; height: 240px; margin: 4px 0;"></a>' % {
                "ll"    : reason["location"],
            }

        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {}

    def parse_sum(self, content_item):
        decline = lambda number, *args: args[0].format(number) if number % 10 == 1 and number % 100 != 11 else args[1].format(number) if number % 10 in [2, 3, 4] and (number % 100 < 10 or number % 100 > 20) else args[2].format(number)
        
        if content_item.data["currency"] == "RUR":
            import re
            return u"<b>%(sum)s %(currency)s</b>" % {
                "sum"       : re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1 ", "%d" % int(abs(content_item.data["sum"]))),
                "currency"  : decline(int(abs(content_item.data["sum"])), u"рубль", u"рубля", u"рублей"),
            }

        return u"<b>%(sum).2f %(currency)s</b>" % {
            "sum"       : abs(content_item.data["sum"]),
            "currency"  : content_item.data["currency"],
        }

    def parse_reason(self, content_item):
        import re                
        import urllib2
        import simplejson

        from config import config
        from utils import urlencode
        from kv import storage as kv_storage
        
        for prefix, formatter in [
            ("ATM", lambda atm: {
                "title"     : u"%(action)s %(sum)s в банкомате <b>%(atm)s</b>" % {
                    "action"    : u"снял" if content_item.data["sum"] < 0 else u"положил",
                    "sum"       : self.parse_sum(content_item),
                    "atm"       : atm,
                },
                "location"  : kv_storage["vtb24_atm_location"].get_or_store(atm, lambda: simplejson.loads(
                    urllib2.urlopen("http://geocode-maps.yandex.ru/1.x/?format=json&geocode=" + urlencode(
                        re.sub("([\W])[A-Z]\.", r"\1", re.sub("^RUS ", "", atm))
                    ) + "&key=").read()
                )["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].replace(" ", ","))
            }),

            ("Balance Enquire", lambda atm: {
                "title" : u"Проверил баланс за %(sum)s в банкомате <b>%(atm)s</b>" % {
                    "sum"       : self.parse_sum(content_item),
                    "atm"       : atm,
                }
            }),

            ("Retail", lambda retail: {
                "title" : u"Совершил покупку на сумму %(sum)s в магазине <b>%(retail)s</b>" % {
                    "sum"       : self.parse_sum(content_item),
                    "retail"    : retail,
                }
            }),

            ("Credit", lambda credit: {
                "title" : u"%(action)s %(sum)s %(office)s" % ({
                    "action"    : u"Потратил" if content_item.data["sum"] < 0 else u"Получил",
                    "sum"       : self.parse_sum(content_item),
                    "office"    : u"через систему <b>«Телебанк»</b>"
                } if "MOSCOW TELEBANK" in credit else {
                    "action"    : u"Снял" if content_item.data["sum"] < 0 else u"Положил",
                    "sum"       : self.parse_sum(content_item),
                    "office"    : u"в отделении <b>%(office)s<b>" % {
                        "office"    : credit
                    }
                })
            }),

            ("Unique", lambda unique: {
                "title" : u"%(action)s %(sum)s %(office)s" % ({
                    "action"    : u"Потратил" if content_item.data["sum"] < 0 else u"Получил",
                    "sum"       : self.parse_sum(content_item),
                    "office"    : u"через систему <b>«Телебанк»</b>"
                } if "MOSCOW TELEBANK" in unique else {
                    "action"    : u"Снял" if content_item.data["sum"] < 0 else u"Положил",
                    "sum"       : self.parse_sum(content_item),
                    "office"    : u"в отделении <b>%(office)s<b>" % {
                        "office"    : unique
                    }
                })
            }),
        ]:
            occurrence = re.search(prefix + " (.+)$", content_item.data["reason"])
            if occurrence:
                return formatter(re.sub(" [0-9]+$", "", occurrence.group(1)))


        return {
            "title" : content_item.data["reason"]
        }
