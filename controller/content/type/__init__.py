#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config

from controller.content.type.post import Type as Post
from controller.content.type.image import Type as Image
from controller.content.type.video import Type as Video
from controller.content.type.chatlog import Type as Chatlog

from controller.content.type.content_consume import Type as ContentConsume
from controller.content.type.fitness_activity import Type as FitnessActivity
from controller.content.type.github_action import Type as GithubAction
from controller.content.type.lastfm_like import Type as LastFM_Like
from controller.content.type.lastfm_start_listen import Type as LastFM_StartListen
from controller.content.type.tcard_trip import Type as TCardTrip
from controller.content.type.tweet import Type as Tweet
from controller.content.type.vk_post import Type as VkPost
from controller.content.type.vtb24_transaction import Type as Vtb24Transaction

from controller.content.model import ContentItem

from social_service import all as all_social_service

all = {
    "blog_post" : {
        "type"      :   Post(),
        "view_url"  :   "blog/post/<url>",
    },
    "gallery_image" : {
        "type"      :   Image(),
        "view_url"  :   "gallery/view/<url>",
    },
    "video" : {
        "type"      :   Video(),
        "view_url"  :   "video/view/<url>",
    },
    "chatlog"   : {
        "type"      :   Chatlog(),
        "view_url"  :   "chatlogs/view/<url>",
    },
    "book"      : {
        "type"      :   Post(),
        "view_url"  :   "library/book/<url>",
    },

    "movie"                 : {
        "type"              :   ContentConsume(
                                    item_cases      = (u"фильм",    u"фильма",  u"фильму",  u"фильм",   u"фильмом",     u"фильме"),
                                    item_mcases     = (u"фильмы",   u"фильмов", u"фильмам", u"фильмы",  u"фильмами",    u"фильмах"),
                                    title_renderer  = lambda **kwargs: u"<b>%(user)s</b> посмотрел <b>%(content)s</b>" % kwargs,
                                    image_directory = "data/movies"
                                )
    },
    "game_session"          : {
        "type"              :   ContentConsume(
                                    item_cases      = (u"сеанс игры",   u"сеанса игры",     u"сеансу игры",     u"сеанс игры",  u"сеансом игры",    u"сеансе игры"),
                                    item_mcases     = (u"сеансы игры",  u"сеансов игры",    u"сеансам игры",    u"сеансы игры", u"сеансами игры",   u"сеансах игры"),
                                    title_renderer  = lambda **kwargs: u"<b>%(user)s</b> играл в <b>%(content)s</b>" % kwargs,
                                    image_directory = "data/games"
                                )
    },
    "fitness_activity"      : {
        "type"              :   FitnessActivity(config.runkeeper_username, config.runkeeper_bearer, config.runkeeper_image_directory),
    },
    "github_action"         : {
        "type"              :   GithubAction(config.github_username),
    },
    "lastfm_like"           : {
        "type"              :   LastFM_Like(all_social_service["last.fm"]),
    },
    "lastfm_start_listen"   : {
        "type"              :   LastFM_StartListen(all_social_service["last.fm"]),
    },
    "tcard_trip"            : {
        "type"              :   TCardTrip(config.tcard_username, config.tcard_session_id, config.tcard_number),
        "permissions"       :   ContentItem.permissions_PRIVATE,
    },
    "tweet"                 : {
        "type"              :   Tweet(all_social_service["twitter"]),
    },
    "vk_post"               : {
        "type"              :   VkPost(config.vk_client_id, config.vk_client_secret, config.vk_user_id, config.vk_user_name, config.vk_user_avatar),
    },
    "vtb24_transaction"     : {
        "type"              :   Vtb24Transaction(config.vtb24_username, config.imap_server, config.imap_login, config.imap_password),
        "permissions"       :   ContentItem.permissions_PRIVATE,
    },
}
