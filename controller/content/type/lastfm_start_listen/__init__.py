#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        service,
        
        item_cases      = (u"первое прослушивание", u"первого прослушивания",   u"первому прослушиванию",   u"первое прослушивание",    u"первым прослушиванием",   u"первом прослушивании"),
        item_mcases     = (u"первые прослушивания", u"первых прослушиваний",    u"первым прослушиваниям",   u"первые прослушивания",    u"первыми прослушиваниями", u"первых прослушиваниях"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.service = service

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.service)

class Formatter(abstract.Formatter):
    def __init__(self, service):
        self.service = service

    def get_title(self, content_item):
        return u"""<a href="%(user_url)s">%(username)s</a> начал слушать <a href="%(artist_url)s">%(artist)s</a>""" % {
            "user_url"      : self.service.network.get_user(self.service.username).get_url(),
            "username"      : self.service.username,

            "artist_url"    : self.service.network.get_artist(content_item.data["artist"]).get_url(),
            "artist"        : content_item.data["artist"],
        }

    def get_image(self, content_item):
        return "/asset/img/social_service/last.fm/48x48.png"

    def get_description(self, content_item, url):
        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        from datetime import datetime
        from utils import urlencode_plus

        d = self._get_scrobble_dict(content_item.data)
        if "totally_first_scrobble" in content_item.data:
            d["totally_first_scrobble"] = self._get_scrobble_dict(dict(content_item.data["totally_first_scrobble"], artist=content_item.data["artist"]))
        return d

    #
    def _get_scrobble_dict(self, scrobble):
        from datetime import datetime
        return {
            "created_at"    : datetime.fromtimestamp(scrobble["uts"]),

            "artist"        : scrobble["artist"],
            "artist_url"    : self.service.network.get_artist(scrobble["artist"]).get_url(),
            "track"         : scrobble["track"],
            "track_url"     : self.service.network.get_track(scrobble["artist"], scrobble["track"]).get_url(),

            "scrobble_url"  : self.service.get_scrobble_url(scrobble["artist"], scrobble["uts"]),            

            "picture"       : self.service.get_artist_image_at(scrobble["artist"], datetime.fromtimestamp(scrobble["uts"])),
        }
