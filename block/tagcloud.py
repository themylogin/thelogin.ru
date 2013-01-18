#!/usr/bin/python
# -*- coding: utf-8 -*-

def block(feed):
    from controller.content import get_content_feeds

    if get_content_feeds()[feed]["url"] == "":
        feed_url = ""
    else:
        feed_url = "/" + get_content_feeds()[feed]["url"]

    import operator
    from db import db
    from sqlalchemy import func
    from controller.content.model import ContentItem, Tag

    tags = db.query(Tag, func.count(ContentItem)).join((ContentItem, Tag.content_items)).filter(ContentItem.type.in_(get_content_feeds()[feed]["types"])).group_by(Tag).order_by(Tag.title).all()
    if tags:
        return {
            "tags"          : tags,
            "biggest_tag"   : max(tags, key=operator.itemgetter(1))[1],
            "feed_url"      : feed_url,
        }
    return None
