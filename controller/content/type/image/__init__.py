#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        item_cases      = (u"изображение",  u"изображения", u"изображению",     u"изображение", u"изображением",    u"изображении"),
        item_mcases     = (u"изображения",  u"изображений", u"изображениям",    u"изображения", u"изображениями",   u"изображениях"),

        directory       = "data/gallery"
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.directory = directory

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.directory)

    def get_editor(self):
        return None

class Formatter(abstract.Formatter):
    def __init__(self, directory):
        self.directory = directory

    def get_title(self, content_item):
        return content_item.data["title"]

    def get_image(self, content_item):
        return "/" + self.directory + "/" + self._get_filename(content_item)

    def get_description(self, content_item, url):
        return content_item.data["title"]

    def get_text(self, content_item, url):
        return content_item.data["text"]

    def get_dict(self, content_item, url):
        import dateutil.parser
        return {
            "directory"     : self.directory,
            "filename"      : self._get_filename(content_item),
            "width"         : content_item.data["width"],
            "height"        : content_item.data["height"],
            "taken_with"    : content_item.data["taken_with"],
            "taken_at"      : dateutil.parser.parse(content_item.data["taken_at"]) if content_item.data["taken_at"] else None,
        }

    """"""
    def _get_filename(self, content_item):
        return content_item.type_key + "." + content_item.data["type"]
