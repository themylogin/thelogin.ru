#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config

from social_service.facebook import Facebook
from social_service.foursquare import Foursquare
from social_service.lastfm import LastFM
from social_service.twitter import Twitter
from social_service.vk import Vk

all = {
    "facebook"      :   Facebook(
                            client_id           = config.facebook_client_id,
                            client_secret       = config.facebook_client_secret,
                        ),
    "foursquare"    :   Foursquare(
                            client_id           = config.foursquare_client_id,
                            client_secret       = config.foursquare_client_secret,
                        ),
    "last.fm"       :   LastFM(
                            api_key             = config.lastfm_api_key,
                            api_secret          = config.lastfm_api_secret,

                            username            = config.lastfm_username,
                            last_fm_thelogin_ru_url = config.last_fm_thelogin_ru_url,
                        ),
    "twitter"       :   Twitter(
                            consumer_key        = config.twitter_oauth_consumer_key,
                            consumer_secret     = config.twitter_oauth_consumer_secret,
                            access_token_key    = config.twitter_access_token_key,
                            access_token_secret = config.twitter_access_token_secret
                        ),
    "vk"            :   Vk(
                            client_id           = config.vk_client_id,
                            client_secret       = config.vk_client_secret,
                        ),
}
