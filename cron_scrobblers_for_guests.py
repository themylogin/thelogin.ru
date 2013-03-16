#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import signal
import subprocess

from config import config
from controller.content.model import ContentItem
from db import db
from middleware.authorization.model import User

if __name__ == "__main__":

    for user in db.query(User):
        if user.settings and user.settings.get("RunScrobbler"):
            last_fm_identity = None
            for identity in user.identities:
                if identity.service == "last.fm":
                    last_fm_identity = identity
                    break
            if last_fm_identity is None:
                break

            last_in = db.query(ContentItem).filter(ContentItem.type == "guest_in",
                                                   ContentItem.type_key.startswith("user=%d," % (user.id,))).order_by(-ContentItem.created_at).first()
            if last_in != None:
                scrobbler_config = "%(path)s/data/%(username)s.conf" % {"path" : config.lastfm_mpdscribble_sk_path, "username" : last_fm_identity.service_data["name"]}
                open(scrobbler_config, "w").write("""
log = syslog
host = """ + config.lastfm_mpd_host + """

[last.fm]
url = http://post.audioscrobbler.com/
username = """ + last_fm_identity.service_data["name"] + """
password = """ + config.lastfm_api_secret + """
api_key  = """ + config.lastfm_api_key + """
sk       = """ + last_fm_identity.service_data["session_key"] + """
journal  = """ + config.lastfm_mpdscribble_sk_path + """/data/""" + last_fm_identity.service_data["name"] + """.journal
""")
                scrobbler_cmd = config.lastfm_mpdscribble_sk_path + "/src/mpdscribble --conf " + scrobbler_config

                scrobbler_pid = None
                for pid in [pid for pid in os.listdir("/proc") if pid.isdigit()]:
                    cmd = open(os.path.join("/proc", pid, "cmdline"), "rb").read().replace("\0", " ").strip()
                    if cmd == scrobbler_cmd:
                        scrobbler_pid = int(pid)
                        break

                last_out = db.query(ContentItem).filter(ContentItem.type == "guest_out",
                                                        ContentItem.type_key.startswith("user=%d," % (user.id,)),
                                                        ContentItem.created_at >= last_in.created_at).order_by(ContentItem.created_at).first()
                if last_out == None:
                    if not scrobbler_pid:
                        subprocess.call(scrobbler_cmd, shell=True)
                else:
                    if scrobbler_pid:
                        os.kill(scrobbler_pid, signal.SIGTERM)
