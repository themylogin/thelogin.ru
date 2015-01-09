#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import func

from db import db
from controller.content import get_content_feeds
from controller.content.model import ContentItem

def block(request, item=None):
    if request.user is None:
        return None

    if item is not None:
        start = item["created_at"]
    else:
        start = datetime.now()
    
    if db.query(func.count(ContentItem)).filter(ContentItem.type.in_(get_content_feeds()["timeline"]["types"]), ContentItem.created_at <= start).scalar() > 0:
        return {
            "start" : start,
        }

    return None
