#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import pylast
import requests
import simplejson
from werkzeug.utils import redirect

from config import config
from kv import storage as kv_storage
from local import local_manager
from log import logger
from threading import Thread
from utils import urlencode

class LastFM:	
    def __init__(self, api_key, api_secret, username, last_fm_thelogin_ru_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.network = pylast.LastFMNetwork(self.api_key, self.api_secret)

        self.username = username

        self.last_fm_thelogin_ru_url = last_fm_thelogin_ru_url
        self.last_fm_thelogin_ru_user_id = self.execute_last_fm_thelogin_ru_query(
            "SELECT * FROM \"user\" WHERE username = :username",
            {"username": self.username}
        )[0]["id"]

    #
    def oauth_initiate(self, callback_url):
        return redirect("%(homepage)s/api/auth/?api_key=%(api)s&cb=%(callback_url)s" % {
            "homepage"      : self.network.homepage,
            "api"           : self.api_key,
            "callback_url"  : urlencode(callback_url),
        })

    def oauth_callback(self, request):        
        sg = pylast.SessionKeyGenerator(self.network)
        sg.web_auth_tokens["fake"] = request.args.get("token")
        sk = sg.get_web_auth_session_key("fake")
        user = {}
        for k in pylast.get_lastfm_network(self.api_key, self.api_secret, session_key=sk).get_authenticated_user()._request("user.getInfo", True).getElementsByTagName('*'):
            if k.firstChild and k.firstChild.nodeValue.strip() != "":
                user[k.tagName] = k.firstChild.nodeValue
        
        return (int(user["id"]), dict(user, session_key=sk))

    def get_user_url(self, service_data):
        return service_data["url"]

    def get_user_name(self, service_data):
        return service_data["name"]

    def get_user_avatar(self, service_data):
        return service_data["image"]

    #
    def get_scrobble_url(self, artist, uts):
        return {
            "last.fm"   : None, # TODO: integration with last.fm.thelogin.ru
            "thelogin"  : "/last.fm/#" + str(uts),
        }

    def get_artist_image_at(self, artist, date):
        kv_key = artist + " @ " + date.strftime("%Y-%m-%d")
        try:
            return kv_storage["last.fm artist image"][kv_key]
        except KeyError:
            if date.strftime("%Y-%m-%d") != datetime.now().strftime("%Y-%m-%d"):
                # Awful, but here kv_storage abstraction "leaks"
                best_timedelta = None
                best_timedelta_v = None
                best_prev_timedelta = None
                best_prev_timedelta_v = None
                for k, v in kv_storage["last.fm artist image"]:
                    probe_artist, probe_datetime = k.rsplit(" @ ", 1)

                    if probe_artist == artist:
                        probe_datetime = datetime.strptime(probe_datetime, "%Y-%m-%d")
                        timedelta = abs(probe_datetime - date)

                        if best_timedelta is None or best_timedelta > timedelta:
                            best_timedelta = timedelta
                            best_timedelta_v = v

                        if probe_datetime < datetime:
                            if best_prev_timedelta is None or best_prev_timedelta > timedelta:
                                best_prev_timedelta = timedelta
                                best_prev_timedelta_v = v
                if best_prev_timedelta:                    
                    logger.info("No last.fm artist '%s' image found at %s, copying previous image with timedelta %s", artist, date.strftime("%Y-%m-%d"), str(best_prev_timedelta))
                    kv_storage["last.fm artist image"][kv_key] = best_prev_timedelta_v
                    return kv_storage["last.fm artist image"][kv_key]
                if best_timedelta:
                    logger.info("No last.fm artist '%s' image found at %s, copying image with timedelta %s", artist, date.strftime("%Y-%m-%d"), str(best_timedelta_v))
                    kv_storage["last.fm artist image"][kv_key] = best_timedelta_v
                    return kv_storage["last.fm artist image"][kv_key]

            network = self.network
            def get_image_for_now():
                kv_storage["last.fm artist image"][kv_key] = network.get_artist(artist).get_cover_image()

            Thread(target=get_image_for_now).start()            
            return config.url + "/asset/img/social_service/last.fm/none.png"

    def execute_last_fm_thelogin_ru_query(self, query, params):
        r = requests.post(
            "%s/api/sql" % self.last_fm_thelogin_ru_url,
            headers={"Content-type": "application/json"},
            data=simplejson.dumps({
                "query": query,
                "params": params,
            })
        )
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception(r.content)
