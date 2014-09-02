#!/usr/bin/python
# -*- coding: utf-8 -*-

from mimetypes import guess_type
import os
from PIL import Image
from PIL.ExifTags import TAGS
import urllib2
import urlparse
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.routing import Rule, Submount
from werkzeug.wrappers import BaseResponse
from werkzeug.wsgi import wrap_file

from config import config
from controller.abstract import Controller as Abstract

class Controller(Abstract):
    def __init__(self, path, allow_internet=False):
        self.path = path
        self.allow_internet = allow_internet

        if allow_internet:
            def internet_image(url, processor=""):
                if not url.startswith(("http://", "https://", "ftp://")):
                    return url

                if is_forbidden_internet_image(url):
                    return url

                return "/" + self.path + ("/" + processor + "/" if processor else "/") + url.replace("://", "/")

            self.export_function(globals(), "internet_image", internet_image)

    def get_routes(self):
        return [
            Submount("/" + self.path if self.path else "", [
                Rule("/<int(max=1920):width>/<path:filename>",                                    endpoint="fit_image"),
                Rule("/<int(max=1920):width>/_/<path:filename>",                                  endpoint="fit_image"),
                Rule("/_/<int(max=1920):height>/<path:filename>",                                 endpoint="fit_image"),
                Rule("/<int(max=1920):width>/<int(max=1920):height>/<path:filename>",             endpoint="fit_image"),
                Rule("/fit/<int(max=1920):width>/<int(max=1920):height>/<path:filename>",         endpoint="fit_image"),
                
                Rule("/min-size/<int(max=1920):size>/<filename>",                                 endpoint="min_size_image"),
                
                Rule("/crop/<int(max=1920):width>/<int(max=1920):height>/<path:filename>",        endpoint="crop_image"),
                Rule("/crop/<any(   'top-left',  'top',      'top-right', "
                                "       'left', 'center',        'right', "
                                "'bottom-left', 'bottom', 'bottom-right'):gravity>"
                     "/<int(max=1920):width>/<int(max=1920):height>/<path:filename>",             endpoint="crop_image"),
                
                Rule("/pad/<int(max=1920):width>/<int(max=1920):height>/<path:filename>",         endpoint="pad_image"),
                Rule("/pad/<color>/<int(max=1920):width>/<int(max=1920):height>/<path:filename>", endpoint="pad_image"),
                
                Rule("/stretch/<int(max=1920):width>/<path:filename>",                            endpoint="stretch_image"),
                Rule("/stretch/<int(max=1920):width>/_/<path:filename>",                          endpoint="stretch_image"),
                Rule("/stretch/_/<int(max=1920):height>/<path:filename>",                         endpoint="stretch_image"),
                Rule("/stretch/<int(max=1920):width>/<int(max=1920):height>/<path:filename>",     endpoint="stretch_image"),

                # will just download from internet if allow_internet is enabled
                Rule("/<path:filename>",                                                          endpoint="pass_image"),
            ])
        ]

    def image_handler(image_handler):
        def request_handler(self, request, **kwargs):
            filename = kwargs["filename"].encode("utf-8")
            path = os.path.join(config.path, self.path, filename)

            if not os.path.exists(path) and "/" in filename and self.allow_internet:
                [proto, etc] = filename.split("/", 1)
                url = proto + "://" + etc + "?" + request.query_string

                if is_forbidden_internet_image(url):
                    raise Forbidden()

                try:
                    data = urllib2.urlopen(urllib2.Request(url.encode("utf-8"))).read()
                except:
                    raise NotFound()

                if not os.path.isdir(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))
                open(path, "w+").write(data)

            if not os.path.exists(path):
                raise NotFound()

            requested_path = request.path[1:]
            if self.path and requested_path.startswith(self.path):
                requested_path = requested_path.replace(self.path, "").strip("/")
            processed_path = os.path.join(config.path, self.path, requested_path.encode("utf-8"))
            if not os.path.exists(processed_path):
                im = Image.open(path)
                exif = im._getexif() if hasattr(im, "_getexif") else None
                if exif:
                    metadata = {TAGS.get(k): v for k, v in exif.iteritems()}
                else:
                    metadata = {}
                if "Orientation" in metadata:
                    orientation = metadata["Orientation"]
                    if orientation == 1:
                        # Nothing
                        im = im.copy()
                    elif orientation == 2:
                        # Vertical Mirror
                        im = im.transpose(Image.FLIP_LEFT_RIGHT)
                    elif orientation == 3:
                        # Rotation 180°
                        im = im.transpose(Image.ROTATE_180)
                    elif orientation == 4:
                        # Horizontal Mirror
                        im = im.transpose(Image.FLIP_TOP_BOTTOM)
                    elif orientation == 5:
                        # Horizontal Mirror + Rotation 90° CCW
                        im = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_90)
                    elif orientation == 6:
                        # Rotation 270°
                        im = im.transpose(Image.ROTATE_270)
                    elif orientation == 7:
                        # Horizontal Mirror + Rotation 270°
                        im = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        # Rotation 90°
                        im = im.transpose(Image.ROTATE_90)

                im_processed = image_handler(self, im, **kwargs)

                if not os.path.isdir(os.path.dirname(processed_path)):
                    os.makedirs(os.path.dirname(processed_path))
                im_processed.save(processed_path, format=im.format, quality=85)

            return BaseResponse(wrap_file(request.environ, open(processed_path, "r")), mimetype=guess_type(processed_path)[0])

        return request_handler

    @image_handler
    def execute_fit_image(self, im, **kwargs):
        image_width = float(im.size[0])
        image_height = float(im.size[1])

        if "width" in kwargs and "height" in kwargs:
            requested_width = float(kwargs["width"])
            requested_height = float(kwargs["height"])

            if image_width / image_height > requested_width / requested_height:
                new_width = requested_width
                new_height = new_width / image_width * image_height
            else:
                new_height = requested_height
                new_width = new_height / image_height * image_width
        elif "width" in kwargs:
            requested_width = float(kwargs["width"])

            new_width = requested_width
            new_height = new_width / image_width * image_height
        elif "height" in kwargs:
            requested_height = float(kwargs["height"])

            new_height = requested_height
            new_width = new_height / image_height * image_width

        if new_width > image_width or new_height > image_height:
            new_width = image_width
            new_height = image_height

        return im.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

    @image_handler
    def execute_min_size_image(self, im, **kwargs):
        image_width = float(im.size[0])
        image_height = float(im.size[1])

        requested_size = float(kwargs["size"])

        if image_width < image_height:
            new_width = requested_size
            new_height = new_width / image_width * image_height
        else:
            new_height = requested_size
            new_width = new_height / image_height * image_width

        if new_width > image_width or new_height > image_height:
            new_width = image_width
            new_height = image_height

        return im.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

    @image_handler
    def execute_crop_image(self, im, **kwargs):
        image_width = float(im.size[0])
        image_height = float(im.size[1])

        requested_width = float(kwargs["width"])
        requested_height = float(kwargs["height"])

        if image_width / image_height > requested_width / requested_height:
            new_uncropped_height = requested_height
            new_uncropped_width = new_uncropped_height / image_height * image_width
        else:
            new_uncropped_width = requested_width
            new_uncropped_height = new_uncropped_width / image_width * image_height
        im_uncropped = im.resize((int(new_uncropped_width), int(new_uncropped_height)), Image.ANTIALIAS)

        if "gravity" in kwargs:
            requested_gravity = kwargs["gravity"]
        else:
            requested_gravity = "center"

        if new_uncropped_width > requested_width:
            if "left" in requested_gravity:
                crop = (0, 0, requested_width, requested_height)
            elif "right" in requested_gravity:
                crop = (new_uncropped_width - requested_width, 0, new_uncropped_width, requested_height)
            else:
                crop = ((new_uncropped_width - requested_width) / 2.0, 0, (new_uncropped_width - requested_width) / 2.0 + requested_width, requested_height)
        elif new_uncropped_height > requested_height:
            if "top" in requested_gravity:
                crop = (0, 0, requested_width, requested_height)
            elif "bottom" in requested_gravity:
                crop = (0, new_uncropped_height - requested_height, requested_width, new_uncropped_height)
            else:
                crop = (0, (new_uncropped_height - requested_height) / 2.0, requested_width, (new_uncropped_height - requested_height) / 2.0 + requested_height)
        else:
            crop = (0, 0, requested_width, requested_height)

        return im_uncropped.crop((int(crop[0]), int(crop[1]), int(crop[2]), int(crop[3])))

    @image_handler
    def execute_pad_image(self, im, **kwargs):
        image_width = float(im.size[0])
        image_height = float(im.size[1])

        requested_width = float(kwargs["width"])
        requested_height = float(kwargs["height"])

        if image_width / image_height > requested_width / requested_height:
            new_width = requested_width
            new_height = new_width / image_width * image_height
        else:
            new_height = requested_height
            new_width = new_height / image_height * image_width

        if new_width > image_width or new_height > image_height:
            new_width = image_width
            new_height = image_height

        if "color" in kwargs:
            requested_color = kwargs["color"]
        else:
            requested_color = "black"

        im_with_fields = Image.new("RGBA", (int(requested_width), int(requested_height)), requested_color)
        im_with_fields.paste(im.resize((int(new_width), int(new_height)), Image.ANTIALIAS), (int((requested_width - new_width) / 2.0), int((requested_height - new_height) / 2.0)))

        return im_with_fields

    @image_handler
    def execute_stretch_image(self, im, **kwargs):
        image_width = float(im.size[0])
        image_height = float(im.size[1])

        if "width" in kwargs and "height" in kwargs:
            new_width = float(kwargs["width"])
            new_height = float(kwargs["height"])
        elif "width" in kwargs:
            requested_width = float(kwargs["width"])

            new_width = requested_width
            new_height = new_width / image_width * image_height
        elif "height" in kwargs:
            requested_height = float(kwargs["height"])

            new_height = requested_height
            new_width = new_height / image_height * image_width

        return im.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

    @image_handler
    def execute_pass_image(self, im, **kwargs):
        return im

def is_forbidden_internet_image(url):
    return urlparse.urlparse(url).netloc.split(":")[0].lower() in config.forbid_internet_image
