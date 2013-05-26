#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import timedelta
from sqlalchemy import func
import time

from social_service import all as all_social_service

def block(to, from_=None, limit=6):
    if from_ is None:
        from_ = to - timedelta(days=7)

    last_fm = all_social_service["last.fm"]
    
    result = {
        "from"      : from_,
        "to"        : to,

        "artists"   : [
            {
                "artist"        : artist,
                "artist_url"    : last_fm.network.get_artist(artist).get_url(),
                "scrobble_url"  : last_fm.get_scrobble_url(artist, min_uts),
                "image"         : last_fm.get_artist_image_at(artist, to),
                "scrobbles"     : scrobbles,
                "min_uts"       : min_uts,
            }
            for artist, scrobbles, min_uts in last_fm.thelogin_db.query(
                last_fm.thelogin_Scrobble.artist,
                func.count(last_fm.thelogin_Scrobble),
                func.min(last_fm.thelogin_Scrobble.uts)
            ).filter(
                last_fm.thelogin_Scrobble.user == last_fm.thelogin_user.id,
                last_fm.thelogin_Scrobble.uts >= time.mktime(from_.timetuple()),
                last_fm.thelogin_Scrobble.uts <= time.mktime(to.timetuple()),
            ).group_by(last_fm.thelogin_Scrobble.artist).order_by(-func.count(last_fm.thelogin_Scrobble))[:limit]
        ],
    }
    if not result["artists"]:
        result = None
    return result
