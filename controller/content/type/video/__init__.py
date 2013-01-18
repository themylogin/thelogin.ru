#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        item_cases      = (u"видео",    u"видео",   u"видео",   u"видео",   u"видео",   u"видео"),
        item_mcases     = (u"видео",    u"видео",   u"видео",   u"видео",   u"видео",   u"видео"),

        directory       = "data/video"
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.directory = directory

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.directory)

class Formatter(abstract.Formatter):
    def __init__(self, directory):
        self.directory = directory

    def get_title(self, content_item):
        return content_item.data["title"]

    def get_image(self, content_item):
        return "/" + self.directory + "/preview/" + content_item.type_key + ".jpg"

    def get_description(self, content_item, url):
        return content_item.data["title"]

    def get_text(self, content_item, url):
        return content_item.data["text"]

    def get_dict(self, content_item, url):
        import dateutil.parser
        return {
            "path"              : "/" + self.directory + "/hd/" + content_item.type_key + ".mp4",
            "preview_directory" : self.directory + "/preview",
            "preview_filename"  : content_item.type_key + ".jpg",
            "width"             : content_item.data["width"],
            "height"            : content_item.data["height"],            
        }
