#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

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

class Formatter(abstract.Formatter):
    def __init__(self, cut_format):
        self.cut_format = cut_format

    def get_title(self, content_item):
        return content_item.data["title"]

    def get_image(self, content_item):
        import re
        match = re.compile("<image.*?/>").match(content_item.data["text"])
        if match:
            from lxml import etree
            return etree.fromstring(match.group(0)).get("src")
        else:
            return None

    def get_description(self, content_item, url):
        return self.get_text(content_item, url).split("</p>")[0]

    def get_text(self, content_item, url):
        return self._full_text(content_item, url)

    def get_dict(self, content_item, url):
        import dateutil.parser
        return {
            "title_html"    :   content_item.data.get("title_html", None),
            "preview"       :   self._preview_text(content_item, url),
            "music"         :   content_item.data.get("music", None),
            "began"         :   {
                                    "at"    : dateutil.parser.parse(content_item.data["began"]["datetime"]),
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
        from text_processor import all as all_text_processors
        for text_processor in all_text_processors:
            text = text_processor(text, url)

        return text
