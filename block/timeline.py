#!/usr/bin/python
# -*- coding: utf-8 -*-

def block(item=None):
    if item is not None:
        start = item["created_at"]
    else:
        from datetime import datetime
        start = datetime.now()

    from db import db    
    from sqlalchemy import func
    from controller.content import get_content_feeds
    from controller.content.model import ContentItem
    if db.query(func.count(ContentItem)).filter(ContentItem.type.in_(get_content_feeds()["timeline"]["types"]), ContentItem.created_at <= start).scalar() > 0:
        return {
            "start" : start,
        }

    return None
