#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import dateutil.parser
import os
from PIL import Image
import re
import subprocess
import time

from config import config
from controller.content.type import abstract
from social_service.runkeeper import HealthGraphClient

class Type(abstract.Type):
    def __init__(
        self,

        username, bearer,
        image_directory,
        
        item_cases      = (u"занятие спортом",  u"занятия спортом",     u"занятию спортом",     u"занятие спортом",     u"занятием спортом",    u"занятии спортом"),
        item_mcases     = (u"занятия спортом",  u"занятий спортом",     u"занятиям спортом",    u"занятия спортом",     u"занятиями спортом",   u"занятиях спортом"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.username = username
        self.bearer = bearer

        self.image_directory = image_directory

    def get_provider(self):
        return Provider(self.bearer, self.image_directory)

    def get_formatter(self):
        return Formatter(self.username, self.image_directory)

    def get_editor(self):
        return None

class Provider(abstract.Provider):
    def __init__(self, bearer, image_directory):
        self.bearer = bearer
        self.image_directory = image_directory

    def provide(self):
        client = HealthGraphClient(self.bearer)

        for activity in client.make_request("/fitnessActivities", media_type="application/vnd.com.runkeeper.FitnessActivityFeed+json")["items"]:
            def create_function(activity):
                def function():
                    data = client.make_request(activity["uri"], media_type="application/vnd.com.runkeeper.FitnessActivity+json")
                    return {
                        "started_at"    : dateutil.parser.parse(data["start_time"]).replace(tzinfo=None),
                        "created_at"    : datetime.now(),
                        "data"          : data,
                        "kv"            : {},
                    }

                return function

            yield self.lazy_provider_item(int(activity["uri"].split("/")[2]), create_function(activity))

    def on_item_inserted(self, content_item):
        filename = os.path.join(config.path, self.image_directory, str(content_item.type_key) + ".png")

        xvfb = subprocess.Popen(["Xvfb", ":20", "-screen", "0", "1600x1200x24", "-fbdir", "/tmp"])
        time.sleep(5)
        openbox = subprocess.Popen(["openbox"], env={"DISPLAY" : ":20"})
        time.sleep(10)
        chromium = subprocess.Popen(["chromium-browser", "--kiosk", content_item.data["activity"]], env={"DISPLAY" : ":20"})
        time.sleep(120)
        subprocess.Popen(["import", "-window", "root", filename], env={"DISPLAY" : ":20"}).communicate()
        chromium.terminate()
        chromium.wait()
        openbox.terminate()
        openbox.wait()
        xvfb.terminate()
        xvfb.wait()

        im = Image.open(filename)
        im.crop((573, 229, 573 + 699, 229 + 759)).save(filename)

class Formatter(abstract.Formatter):
    def __init__(self, username, image_directory):
        self.username = username
        self.image_directory = image_directory

    def get_title(self, content_item):
        return """<a href="http://runkeeper.com/user/%(user_id)s">%(username)s</a> """ % {
            "user_id"   : content_item.data["userID"],
            "username"  : self.username,
        } + {
            "Cycling"   :   lambda: u"проехал <b>%(total_distance).2f км</b> за %(time_period)s (<b>%(speed).2f км/ч</b>)" % {
                                "total_distance"    : content_item.data["total_distance"] / 1000.0,
                                "time_period"       : self.time_period(content_item.data["duration"]),
                                "speed"             : content_item.data["total_distance"] * 3.6 / content_item.data["duration"],
                            },
            "Running"   :   lambda: u"пробежал <b>%(total_distance).2f км</b> за %(time_period)s (<b>%(speed).2f км/ч</b>)" % {
                                "total_distance"    : content_item.data["total_distance"] / 1000.0,
                                "time_period"       : self.time_period(content_item.data["duration"]),
                                "speed"             : content_item.data["total_distance"] * 3.6 / content_item.data["duration"],
                            },
        }[content_item.data["type"]]()

    def get_image(self, content_item):
        return "/asset/img/social_service/runkeeper/activity/" + content_item.data["type"] + "/48x48.png"

    def get_description(self, content_item, url):        
        return """<a class="block" href="%(url)s"><img class="block" src="%(image)s"></a>""" % {
            "url"   : content_item.data["activity"],
            "image" : "/" + self.image_directory + "/" + str(content_item.type_key) + ".png",
        }

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {
            "images"    : content_item.data["images"],
            "notes"     : content_item.data.get("notes", ""),
        }

    #
    def time_period(self, seconds):
        return "%(h)2d:%(m)02d:%(s)02d" % { "h" : int(seconds / 60 / 60), "m" : int(seconds / 60 % 60), "s" : int(seconds % 60) }
