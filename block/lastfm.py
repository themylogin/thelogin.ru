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
                "artist"        : artist["artist"],
                "artist_url"    : last_fm.network.get_artist(artist["artist"]).get_url(),
                "scrobble_url"  : last_fm.get_scrobble_url(artist["artist"], artist["min_uts"]),
                "image"         : last_fm.get_artist_image_at(artist["artist"], to),
                "scrobbles"     : artist["scrobbles"],
                "min_uts"       : artist["min_uts"],
            }
            for artist in last_fm.execute_last_fm_thelogin_ru_query(
                """
                    SELECT artist,
                           COUNT(scrobble.id) AS scrobbles,
                           MIN(scrobble.uts) AS min_uts
                    FROM scrobble
                    WHERE user_id = :user_id
                      AND uts >= :from
                      AND uts <= :to
                    GROUP BY artist
                    ORDER BY COUNT(scrobble.id) DESC
                    LIMIT :limit
                """,
                {
                    "user_id": last_fm.last_fm_thelogin_ru_user_id,
                    "from": time.mktime(from_.timetuple()),
                    "to": time.mktime(to.timetuple()),
                    "limit": limit,
                }
            )
        ],
    }
    if not result["artists"]:
        result = None
    return result
