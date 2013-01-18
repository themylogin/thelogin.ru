#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        item_cases,
        item_mcases,

        title_renderer,
        image_directory
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.title_renderer = title_renderer
        self.image_directory = image_directory

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.title_renderer, self.image_directory)

class Formatter(abstract.Formatter):
    def __init__(self, title_renderer, image_directory):
        self.title_renderer = title_renderer
        self.image_directory = image_directory

    def get_title(self, content_item):
        return self.title_renderer(user="themylogin", content=content_item.data["title"])

    def get_image(self, content_item):
        return "/asset/img/content/type/content_consume/" + content_item.type + "/48x48.png"

    def get_description(self, content_item, url):
        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        from datetime import datetime
        from utils import urlencode
        return {
            "download"          :   datetime.fromtimestamp(content_item.data["download"]) if "download" in content_item.data else None,
            "start"             :   datetime.fromtimestamp(content_item.data["start"]) if "start" in content_item.data else None,
            "image_directory"   :   self.image_directory,
            "images"            :   map(urlencode, content_item.data.get("screenshots", [content_item.data["title"] + "." + str(i) + ".jpg" for i in range(1, 5)]))
        }
