#!/usr/bin/python
# -*- coding: utf-8 -*-

all = {
    "index"     : {
        "title"     : u"Лента",
        "url"       : "",
        "types"     : ["blog_post", "gallery_image", "video", "chatlog", "shop_product", "library_book"],
    },
    "blog"      : {
        "title"     : u"Блог",
        "url"       : "blog",
        "types"     : ["blog_post"],
    },
    "gallery"   : {
        "title"     : u"Галерея",
        "url"       : "gallery",
        "types"     : ["gallery_image"],
        "per_page"  : 40,
    },
    "video"     : {
        "title"     : u"Видео",
        "url"       : "video",
        "types"     : ["video"],
    },
    "chatlogs"  : {
        "title"     : u"Логи",
        "url"       : "chatlogs",
        "types"     : ["chatlog"],
    },
    "shop"      : {
        "title"     : u"Продам",
        "url"       : "shop",
        "types"     : ["shop_product"],
    },
    "library"   : {
        "title"     : u"Библиотека",
        "url"       : "library",
        "types"     : ["library_book"],
    },

    "timeline"  : {
        "url"       : "timeline",
        "types"     : ["movie", "game_session", "fitness_activity", "github_action", "lastfm_like", "lastfm_start_listen", "tcard_trip", "tweet", "vk_post", "vtb24_transaction"],
        "rss_allow" : False,
    }
}
