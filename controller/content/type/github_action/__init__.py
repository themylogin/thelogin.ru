#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime        
import feedparser
import re
from time import mktime

from config import config
from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        username,
        
        item_cases      = (u"коммит",   u"коммита",     u"коммиту",     u"коммит",  u"коммитом",    u"коммите"),
        item_mcases     = (u"коммиты",  u"коммитов",    u"коммитам",    u"коммиты", u"коммитами",   u"коммитах"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.username = username

    def get_provider(self):
        return Provider(self.username)

    def get_formatter(self):
        return Formatter()

    def get_editor(self):
        return None

class Provider(abstract.Provider):
    def __init__(self, username):
        self.username = username

    def provide(self):
        for item in feedparser.parse("https://github.com/" + self.username + ".atom")["entries"]:
            yield self.provider_item(
                id          =   int(item["id"].split("/")[1]),
                created_at  =   datetime.fromtimestamp(mktime(item["published_parsed"])).replace(tzinfo=None) + config.timezone,
                data        =   dict([(k,v) for (k,v) in item.items() if isinstance(v, unicode)]),
                kv          =   {},
            )

class Formatter(abstract.Formatter):
    def __init__(self):
        pass

    def get_title(self, content_item):
        return re.search(r"""<div class="title">(.+?)[^<>]+</div>""", self.summary(content_item), re.DOTALL).group(1)

    def get_image(self, content_item):
        return "/asset/img/social_service/github/48x48.png"

    def get_description(self, content_item, url):        
        text = self.summary(content_item)
        text = re.compile(r"""<a[^<>]+class="gravatar"(.+?)</a>""", re.DOTALL).sub(r"", text)
        text = re.compile(r"""<div class="title">(.+?)[^<>]+</div>""", re.DOTALL).sub(r"", text)
        text = re.compile(r"""<a [^<>]+ class="committer">.+</a> committed """).sub(r"", text)
        # text = text.replace("<div class=\"details\">", "<div class=\"text\">")
        text = re.compile(r"""<div class="time">(.+?)</div>""", re.DOTALL).sub(r"", text)
        return text

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {}

    def summary(self, content_item):
        return content_item.data.get("summary", content_item.data.get("subtitle"))
