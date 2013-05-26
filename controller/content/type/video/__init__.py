#!/usr/bin/python
# -*- coding: utf-8 -*-

import dateutil.parser
import os.path
from PIL import Image
import re
import subprocess

from config import config
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

    def get_editor(self):
        return Editor(self.directory)

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
        return {
            "path"              : "/" + self.directory + "/hd/" + content_item.type_key + ".mp4",
            "preview_directory" : self.directory + "/preview",
            "preview_filename"  : content_item.type_key + ".jpg",
            "width"             : content_item.data["width"],
            "height"            : content_item.data["height"],            
        }

class Editor(abstract.Editor):
    def __init__(self, directory):
        self.directory = directory

    def new_db(self):
        return {
            "title"         : "",
            "text"          : "",

            "fps"           : 0,
            "width"         : 1,
            "height"        : 1,
            "filesize"      : 0,
            "type"          : "",
        }

    def db_to_form(self, db_data):
        if db_data["type"]:
            def size_multiple_of_16(size):
                return map(lambda number: number + (16 - number % 16) if number % 16 else number, size)
            size = size_multiple_of_16((db_data["width"], db_data["height"]))

            db_data["pre"] = """avconv -i %(path)s/original/%(id)d.%(type)s -s %(width)dx%(height)d -y -f mp4 -vcodec libx264 -crf 28 -threads 0 -flags +loop -cmp +chroma -deblockalpha -1 -deblockbeta -1 -refs 3 -bf 3 -coder 1 -me_method hex -me_range 18 -subq 7 -partitions +parti4x4+parti8x8+partp8x8+partb8x8 -g 320 -keyint_min 25 -level 41 -qmin 10 -qmax 51 -qcomp 0.7 -trellis 1 -sc_threshold 40 -i_qfactor 0.71 -flags2 +mixed_refs+dct8x8+wpred+bpyramid -strict experimental -acodec aac -ab 320k -ar 44100 -ac 2 temp.mp4
qt-faststart temp.mp4 %(path)s/hd/%(id)d.mp4
rm temp.mp4""" % {
            "path"  : os.path.join(config.path, self.directory),
            "id"    : 70,
            "type"  : db_data["type"],
            "width" : size[0],
            "height": size[1],
        }

        return db_data

    def form_to_db(self, request, db_data):
        for k in ["title", "text"]:
            db_data[k] = request.form["data[" + k + "]"]

        if "image" in request.files and request.files["image"].filename:
            image = request.files["image"]
            filename = os.path.join(config.path, self.directory, "preview", request.form["type_key"] + ".jpg")
            open(filename, "w+").write(request.files["image"].read())

        if "video" in request.files and request.files["video"].filename:
            video = request.files["video"]

            db_data["type"] = video.filename.split(".")[-1].lower()
            filename = os.path.join(config.path, self.directory, "original", request.form["type_key"] + "." + db_data["type"])

            open(filename, "w+").write(video.read())

            db_data["filesize"] = os.path.getsize(filename)

            information = subprocess.Popen(["avconv", "-i", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[1]
            db_data["width"], db_data["height"] = map(int, re.findall("(\d+)x(\d+)", information)[0])
            db_data["fps"] = float(re.findall("([\d.]+) tbr", information)[0])

        return db_data
