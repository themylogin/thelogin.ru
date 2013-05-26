#!/usr/bin/python
# -*- coding: utf-8 -*-

import dateutil.parser
from lxml import etree
import re

from controller.content.type import abstract
from controller.content.type.post.text_processor import all as all_text_processors

class Type(abstract.Type):
    def __init__(
        self,

        item_cases      = (u"пост",     u"поста",       u"посту",       u"пост",        u"постом",      u"посте"),
        item_mcases     = (u"посты",    u"постов",      u"постам",      u"посты",       u"постами",     u"постах"),

        cut_format      = u"(<a href=\"%(url)s\">Далее</a>)"
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.cut_format = cut_format

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.cut_format)

    def get_editor(self):
        return Editor()

class Formatter(abstract.Formatter):
    def __init__(self, cut_format):
        self.cut_format = cut_format

    def get_title(self, content_item):
        return content_item.data["title"]

    def get_image(self, content_item):        
        match = re.compile("<image.*?/>").match(content_item.data["text"])
        if match:
            return etree.fromstring(match.group(0)).get("src")
        else:
            return None

    def get_description(self, content_item, url):
        return self.get_text(content_item, url).split("</p>")[0]

    def get_text(self, content_item, url):
        return self._full_text(content_item, url)

    def get_dict(self, content_item, url):
        return {
            "title_html"    :   content_item.data.get("title_html", None),
            "preview"       :   self._preview_text(content_item, url),
            "music"         :   content_item.data.get("music", None),
            "began"         :   {
                                    "at"    : content_item.started_at,
                                    "music" : content_item.data["began"].get("music", None),
                                }
                                if "began" in content_item.data
                                else None,                                
        }

    """"""
    def _preview_text(self, content_item, url):
        text = content_item.data["text"]
        if "<cut>" in text:
            text = text.split("<cut>")[0] + " " + self.cut_format % {
                "url"   : url,
            } + "</p>"
        return self._parse_text(text, url)

    def _full_text(self, content_item, url):
        text = content_item.data["text"]
        return self._parse_text(text, url).replace("<cut>", "")

    def _parse_text(self, text, url):
        for text_processor in all_text_processors:
            text = text_processor(text, url)

        return text

class Editor(abstract.Editor):
    def new_db(self):
        return {
            "title"         : "",
            "title_html"    : "",
            "music"         : "",
            "text"          : "",
            
            "ipaddress"     : "",
            "useragent"     : "",
        }

    def db_to_form(self, db_data):
        return db_data

    def form_to_db(self, request, db_data):
        db_data["ipaddress"] = db_data.get("ipaddress", request.remote_addr)
        db_data["useragent"] = db_data.get("useragent", request.user_agent.string)

        for k in ["title",
                  "title_html",
                  "music",
                  "text"]:
            db_data[k] = request.form["data[" + k + "]"]

        db_data["began"] = {"music" : request.form["data[started_at_music]"]}

        return db_data
