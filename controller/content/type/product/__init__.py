#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path

from config import config
from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        item_cases      = (u"товар",    u"товара",      u"товару",      u"товар",       u"товаром",     u"товаре"),
        item_mcases     = (u"товары",   u"товаров",     u"товарам",     u"товары",      u"товарами",    u"товарах"),

        image_dir       = "data/shop"
    ):
        super(Type, self).__init__(item_cases, item_mcases)

        self.image_dir = image_dir

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.image_dir)

    def get_editor(self):
        return Editor(self.image_dir)

class Formatter(abstract.Formatter):
    def __init__(self, image_dir):
        self.image_dir = image_dir

    def get_title(self, content_item):
        return content_item.data["title"]

    def get_image(self, content_item):
        return "/" + self.image_dir + "/" + content_item.type_key + "." + content_item.data["image_type"]

    def get_description(self, content_item, url):
        return content_item.data["text"]

    def get_text(self, content_item, url):
        return content_item.data["text"]

    def get_dict(self, content_item, url):
        return {
            "image_template"    : "/" + self.image_dir + "/%s/" + content_item.type_key + "." + content_item.data["image_type"],
            "sold"              : content_item.data["sold"],
        }

class Editor(abstract.Editor):
    def __init__(self, image_dir):
        self.image_dir = image_dir

    def new_db(self):
        return {
            "title"         : "",
            "text"          : "",
            "image_type"    : "",
            "sold"          : False,
        }

    def db_to_form(self, db_data):
        return db_data

    def form_to_db(self, request, db_data):
        for k in ["title", "text"]:
            db_data[k] = request.form["data[" + k + "]"]

        if "image" in request.files and request.files["image"].filename:
            image = request.files["image"]

            db_data["image_type"] = image.filename.split(".")[-1].lower()
            open(os.path.join(config.path, self.image_dir, request.form["type_key"] + "." + db_data["image_type"]), "w+").write(image.read())

        db_data["sold"] = "data[sold]" in request.form

        return db_data
