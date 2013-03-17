#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import time
from urlparse import urlparse
from werkzeug.routing import Rule, Subdomain
from werkzeug.wrappers import Response

from config import config
from controller.image import Controller as Image

class Controller(Image):
    def __init__(self, path, subdomain, **kwargs):
        self.subdomain = subdomain
        super(Controller, self).__init__(path, **kwargs)

    def get_routes(self):
        p = self.path
        self.path = ""
        image_routes = super(Controller, self).get_routes()
        self.path = p

        return [
            Subdomain(self.subdomain, image_routes + [
                Rule("/",                   endpoint="index"),
            ])            
        ]

    def execute_index(self, request):
        if request.method == "POST":
            extension = request.files["Filedata"].filename.split(".")[-1].lower()
            if extension == "jpeg":
                extension = "jpg"

            if extension in ["gif", "jpg", "png"]:
                filename = str(time.time()).replace(".", "").ljust(12, "0") + "." + extension
                open(os.path.join(config.path, self.path, filename), "w+").write(request.files["Filedata"].read())                
                return Response(filename)
            else:
                return Response("")
        else:
            return self.render_to_response(request, "imagehosting/index.html", **{
                "host"          :   self.subdomain + "." + urlparse(config.url).netloc.split(":")[0],
                "parent_host"   :   urlparse(config.url).netloc.split(":")[0],
            })
