#!/usr/bin/python
# -*- coding: utf-8 -*-

from werkzeug.utils import escape

from config import config
from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        item_cases      = (u"лог",      u"лога",    u"логу",    u"лог",     u"логом",   u"логе"),
        item_mcases     = (u"логи",     u"логов",   u"логам",   u"логи",    u"логами",  u"логах"),

        cut_format      = u"(<a href=\"%(url)s\">Далее</a>)"
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter()

    def get_editor(self):
        return None

class Formatter(abstract.Formatter):
    def get_title(self, content_item):
        return u"Лог №%s" % (content_item.type_key,)

    def get_image(self, content_item):
        return None

    def get_description(self, content_item, url):
        return self.get_text(content_item, url)        

    def get_text(self, content_item, url):
        text = content_item.data["text"]
        text = escape(text).replace("\n", "<br />\n")
        for smilie in config.smilies:
            text = text.replace(escape(smilie), '<img class="smilie" src="' + config.url + config.smilies[smilie] + '" />')
        return text

    def get_dict(self, content_item, url):
        return {
            "rating"    : sum([vote[0] for vote in content_item.data["rating"]]),
        }
