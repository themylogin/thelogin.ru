#!/usr/bin/python
# -*- coding: utf-8 -*-

from controller.authorization import Controller as Authorization
from controller.content import Controller as Content
from controller.image import Controller as Image
from controller.imagehosting import Controller as ImageHosting
from controller.smarthome_api import Controller as SmarthomeApi

from controller.content.type import all as all_content_types
from controller.content.feed import all as all_content_feeds
from social_service import all as all_social_services

all = [
    Authorization(all_social_services),
    Content(all_content_types, all_content_feeds),
    Image("data/blog/images"),
    Image("data/gallery"),
    Image("data/games"),
    Image("data/internet", allow_internet=True),
    Image("data/library"),
    Image("data/movies"),
    Image("data/music"),
    Image("data/runkeeper"),
    Image("data/shop"),
    Image("data/video/preview"),
    ImageHosting("data/i", "i"),
    SmarthomeApi(),
]
