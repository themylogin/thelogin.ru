#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path

from config import config
from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        item_cases      = (u"книга",    u"книги",       u"книге",       u"книгу",       u"книгой",      u"книге"),
        item_mcases     = (u"книги",    u"книг",        u"книгам",      u"книги",       u"книгами",     u"книгах"),

        image_dir       = "data/library"
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
            "book_type"         : content_item.data["book_type"],
        }

class Editor(abstract.Editor):
    def __init__(self, image_dir):
        self.image_dir = image_dir

    def db_to_form(self, db_data):
        return db_data

    def form_to_db(self, request, db_data):
        for k in ["title", "text"]:
            db_data[k] = request.form["data[" + k + "]"]

        if "image" in request.files and request.files["image"].filename:
            image = request.files["image"]

            db_data["image_type"] = image.filename.split(".")[-1].lower()
            open(os.path.join(config.path, self.image_dir, request.form["type_key"] + "." + db_data["image_type"]), "w+").write(image.read())

        if "book" in request.files and request.files["book"].filename:
            book = request.files["book"]

            db_data["book_type"] = book.filename.split(".")[-1].lower()
            open(os.path.join(config.path, self.image_dir, request.form["type_key"] + "." + db_data["book_type"]), "w+").write(book.read())

        return db_data
