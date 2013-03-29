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

    def get_editor(self):
        return None

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

            import email
            email_message = email.message_from_string(raw_email)
            maintype = email_message.get_content_maintype()
            if maintype == "multipart":
                text = ""
                for part in email_message.get_payload():
                    if part.get_content_maintype() == "text":
                        text += part.get_payload(decode=True)
            elif maintype == "text":
                text = email_message.get_payload(decode=True)
            text = text.decode("utf-8")

            if u"произведена транзакция" not in text:
                continue

            import re
            import datetime
            import dateutil.parser
            from config import config
            data = re.search(u"([0-9.]+) в ([0-9:]+)", text)
            yield self.provider_item(
                id          =   uid,
                created_at  =   dateutil.parser.parse(data.group(1) + " " + data.group(2), dayfirst=True) - datetime.timedelta(hours=4) + config.timezone,
                data        =   { "notification" : text },
                kv          =   {}
            )

    def is_not_actual_item(self, content_item):
        return False

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
            from controller.content.utils import timeline_map
            return timeline_map(reason["location"])

        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {}

    def parse_sum(self, content_item):
        return self.format_sum(content_item.data["sum"], content_item.data["currency"])

    def format_sum(self, sum, currency):
        decline = lambda number, *args: args[0].format(number) if number % 10 == 1 and number % 100 != 11 else args[1].format(number) if number % 10 in [2, 3, 4] and (number % 100 < 10 or number % 100 > 20) else args[2].format(number)

        if currency == "RUR":
            import re
            return u"<b>%(sum)s %(currency)s</b>" % {
                "sum"       : re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1 ", "%d" % int(abs(sum))),
                "currency"  : decline(int(abs(sum)), u"рубль", u"рубля", u"рублей"),
            }

        return u"<b>%(sum).2f %(currency)s</b>" % {
            "sum"       : abs(sum),
            "currency"  : currency,
        }

    def parse_reason(self, content_item):
        import re                
        import urllib2
        import simplejson

        from config import config
        from utils import urlencode
        from kv import storage as kv_storage

        if "notification" in content_item.data:
            m = re.search(re.compile(u"произведена транзакция по (.+) на сумму ([0-9.]+) (.+?)\..+Детали платежа: (.+)\. Код авторизации", re.DOTALL), content_item.data["notification"])
            return {
                u"зачислению средств"   : lambda **kwargs: {
                    "title"     : u"Положил %(sum)s в отделении <b>%(details)s</b>" % kwargs if "TELEBANK" not in kwargs["details"] else u"Получил %(sum)s через систему <b>«Телебанк»</b>" % kwargs,
                },
                u"снятию средств"       : lambda **kwargs: {
                    "title"     : u"Снял %(sum)s в отделении <b>%(details)s</b>" % kwargs if "TELEBANK" not in kwargs["details"] else u"Снял %(sum)s через систему <b>«Телебанк»</b>" % kwargs,
                },

                u"снятию наличных"      : lambda **kwargs: {
                    "title"     : u"Снял %(sum)s в банкомате <b>%(details)s</b>" % kwargs,
                    "location"  : kv_storage["vtb24_atm_location"].get_or_store(kwargs["details"], lambda: simplejson.loads(
                        urllib2.urlopen("http://geocode-maps.yandex.ru/1.x/?format=json&geocode=" + urlencode("NOVOSIBIRSK " + kwargs["details"]) + "&key=").read()
                    )["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].replace(" ", ",")),
                },
                    
                u"оплате"               : lambda **kwargs: {
                    "title"     : u"Совершил покупку на сумму %(sum)s в магазине <b>%(details)s</b>" % kwargs,
                },
            }[m.group(1)](**{
                "sum"       : self.format_sum(float(m.group(2)), m.group(3)),
                "details"   : m.group(4),
            })

        # support old transactions parsed from monthly cardman@plcmail.vtb24.ru statements
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
