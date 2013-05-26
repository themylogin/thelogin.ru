#!/usr/bin/python
# -*- coding: utf-8 -*-

import operator
from sqlalchemy import func

from controller.content import get_content_feeds
from controller.content.model import ContentItem, Tag
from db import db

def block(feed):
    if get_content_feeds()[feed]["url"] == "":
        feed_url = ""
    else:
        feed_url = "/" + get_content_feeds()[feed]["url"]

    tags = db.query(Tag, func.count(ContentItem)).join((ContentItem, Tag.content_items)).filter(ContentItem.type.in_(get_content_feeds()[feed]["types"])).group_by(Tag).order_by(Tag.title).all()
    if tags:
        return {
            "tags"          : tags,
            "biggest_tag"   : max(tags, key=operator.itemgetter(1))[1],
            "feed_url"      : feed_url,
        }
    return None
