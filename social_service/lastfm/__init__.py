#!/usr/bin/python
# -*- coding: utf-8 -*-

class LastFM:	
    def __init__(self, api_key, api_secret, username, thelogin_path=None):        
        import pylast
        self.api_key = api_key
        self.api_secret = api_secret
        self.network = pylast.LastFMNetwork(self.api_key, self.api_secret)

        self.username = username

        import sys
        sys.path.append(thelogin_path)
        from lastfm.models import DBSession, User, Scrobble
        sys.path.pop()
        self.thelogin_db = DBSession
        self.thelogin_User = User
        self.thelogin_Scrobble = Scrobble
        import os.path
        import paste.deploy
        from sqlalchemy import engine_from_config
        self.thelogin_db.configure(bind=engine_from_config(paste.deploy.appconfig("config://" + os.path.join(thelogin_path, "production.ini")), 'sqlalchemy.'))
        self.thelogin_user = self.thelogin_db.query(self.thelogin_User).filter(self.thelogin_User.username == self.username)[0]

    #
    def oauth_initiate(self, callback_url):
        from werkzeug.utils import redirect
        from utils import urlencode
        return redirect("%(homepage)s/api/auth/?api_key=%(api)s&cb=%(callback_url)s" % {
            "homepage"      : self.network.homepage,
            "api"           : self.api_key,
            "callback_url"  : urlencode(callback_url),
        })

    def oauth_callback(self, request):
        import pylast
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
        from kv import storage as kv_storage
        from datetime import datetime

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
                    from log import logger
                    logger.info("No last.fm artist '%s' image found at %s, copying previous image with timedelta %s", artist, date.strftime("%Y-%m-%d"), str(best_prev_timedelta))
                    kv_storage["last.fm artist image"][kv_key] = best_prev_timedelta_v
                    return kv_storage["last.fm artist image"][kv_key]
                if best_timedelta:
                    from log import logger
                    logger.info("No last.fm artist '%s' image found at %s, copying image with timedelta %s", artist, date.strftime("%Y-%m-%d"), str(best_timedelta_v))
                    kv_storage["last.fm artist image"][kv_key] = best_timedelta_v
                    return kv_storage["last.fm artist image"][kv_key]

            network = self.network
            def get_image_for_now():
                kv_storage["last.fm artist image"][kv_key] = network.get_artist(artist).get_cover_image()

            from threading import Thread
            Thread(target=get_image_for_now).start()
            from config import config
            return config.url + "/asset/img/social_service/last.fm/none.png"
