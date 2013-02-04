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
        pass

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
        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {}

    def parse_sum(self, content_item):
        decline = lambda number, *args: args[0].format(number) if number % 10 == 1 and number % 100 != 11 else args[1].format(number) if number % 10 in [2, 3, 4] and (number % 100 < 10 or number % 100 > 20) else args[2].format(number)
        
        if content_item.data["currency"] == "RUR":
            return u"<b>%(sum)d</b> %(currency)s" % {
                "sum"       : int(abs(content_item.data["sum"])),
                "currency"  : decline(int(abs(content_item.data["sum"])), u"рубль", u"рубля", u"рублей"),
            }

        return u"<b>%(sum).2f</b> %(currency)s" % {
            "sum"       : abs(content_item.data["sum"]),
            "currency"  : content_item.data["currency"],
        }

    def parse_reason(self, content_item):
        import re
        
        atm = re.search("ATM (.+) ([0-9]+)$", content_item.data["reason"])
        if atm:
            return {
                "title" : u"%(action)s %(sum)s в банкомате <b>%(atm)s</b>" % {
                    "action"    : u"снял" if content_item.data["sum"] < 0 else u"положил",
                    "sum"       : self.parse_sum(content_item),
                    "atm"       : atm.group(1),
                }
            }

        retail = re.search("Retail (.+) ([0-9]+)$", content_item.data["reason"])
        if retail:
            return {
                "title" : u"Совершил покупку на сумму %(sum)s в магазине <b>%(retail)s</b>" % {
                    "sum"       : self.parse_sum(content_item),
                    "atm"       : retail.group(1),                
                }
            }

        return {
            "title" : content_item.data["reason"]
        }
