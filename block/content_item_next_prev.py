#!/usr/bin/python
# -*- coding: utf-8 -*-

def block(request, feed, item):
    from db import db
    from controller.content.model import ContentItem
    from controller.content import get_content_feeds, process_content_item
    
    next = db.query(ContentItem).filter(ContentItem.type.in_(get_content_feeds()[feed]["types"]), ContentItem.permissions_for(request.user), ContentItem.created_at > item["created_at"]).order_by(ContentItem.created_at).first()
    prev = db.query(ContentItem).filter(ContentItem.type.in_(get_content_feeds()[feed]["types"]), ContentItem.permissions_for(request.user), ContentItem.created_at < item["created_at"]).order_by(-ContentItem.created_at).first()
    if next or prev:
        return {
            "next"  : process_content_item(next) if next else None,
            "prev"  : process_content_item(prev) if prev else None,
        }
    else:
        return None
