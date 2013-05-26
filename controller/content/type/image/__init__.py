#!/usr/bin/python
# -*- coding: utf-8 -*-

import dateutil.parser
import os.path
from PIL import Image
from PIL.ExifTags import TAGS

from config import config
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
        return Editor(self.directory)

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

class Editor(abstract.Editor):
    def __init__(self, directory):
        self.directory = directory

    def new_db(self):
        return {
            "title"         : "",
            "text"          : "",

            "type"          : "",
            "width"         : 1,
            "height"        : 1,
            "taken_with"    : "",
            "taken_at"      : "",
        }

    def db_to_form(self, db_data):
        return db_data

    def form_to_db(self, request, db_data):
        for k in ["title", "text"]:
            db_data[k] = request.form["data[" + k + "]"]

        if "image" in request.files and request.files["image"].filename:
            image = request.files["image"]

            db_data["type"] = image.filename.split(".")[-1].lower()
            filename = os.path.join(config.path, self.directory, request.form["type_key"] + "." + db_data["type"])

            open(filename, "w+").write(image.read())

            im = Image.open(filename)
            db_data["width"], db_data["height"] = im.size

            for tag, value in im._getexif().items():
                decoded = TAGS.get(tag, tag)
                
                if decoded in ["DateTimeDigitized", "DateTimeOriginal", "DateTime"]:
                    db_data["taken_at"] = value.replace(":", "-", 2)
                if decoded == "Model":
                    db_data["taken_with"] = value

        for k in ["taken_at", "taken_with"]:
            if request.form.get("data[" + k + "]", None):
                db_data[k] = request.form["data[" + k + "]"]

        return db_data
