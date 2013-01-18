#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.content.type import abstract

class Type(abstract.Type):
    def __init__(
        self,

        service,
        
        item_cases      = (u"любимый трек",     u"любимого трека",  u"любимому треку",  u"любимый трек",    u"любимым треком",      u"любимом треке"),
        item_mcases     = (u"любимые треки",    u"любимых треков",  u"любимым трекам",  u"любимые треки",   u"любимыми треками",    u"любимых треках"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.service = service

    def get_provider(self):
        return Provider(self.service)

    def get_formatter(self):
        return Formatter(self.service)

class Provider(abstract.Provider):
    def __init__(self, service):
        self.service = service

    def provide(self):
        from datetime import datetime
        for track in self.service.network.get_user(self.service.username).get_loved_tracks():
            yield self.provider_item(
                id          =   int(track.timestamp),
                created_at  =   datetime.fromtimestamp(int(track.timestamp)),
                data        =   {
                                    "artist"    : track.track.artist.name,
                                    "title"     : track.track.title
                                },
                kv          =   {},
            )


class Formatter(abstract.Formatter):
    def __init__(self, service):
        self.service = service

    def get_title(self, content_item):
        return u"""<a href="%(url)s">%(username)s</a> добавил в <a href="%(url)s/library/loved">любимые композиции</a>""" % {
            "url"       : self.service.network.get_user(self.service.username).get_url(),
            "username"  : self.service.username,
        }

    def get_image(self, content_item):
        return "/asset/img/social_service/last.fm/48x48.png"

    def get_description(self, content_item, url):
        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {
            "artist"        : content_item.data["artist"],
            "artist_url"    : self.service.network.get_artist(content_item.data["artist"]).get_url(),
            "track"         : content_item.data["title"],
            "track_url"     : self.service.network.get_track(content_item.data["artist"], content_item.data["title"]).get_url(),
        }
