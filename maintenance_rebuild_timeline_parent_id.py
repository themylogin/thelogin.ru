#!/usr/bin/python
# -*- coding: utf-8 -*-

from db import db
from controller.content.feed import all as all_feed
from controller.content.model import ContentItem

if __name__ == "__main__":
    for content_item in db.query(ContentItem):
        content_item.parent_id = None
    db.flush()

    for parent in db.query(ContentItem).filter(ContentItem.type.in_(all_feed["timeline"]["types"])):
        if parent.started_at and parent.created_at:
            for child in db.query(ContentItem).filter(ContentItem.type.in_(all_feed["timeline"]["types"]), parent.started_at < ContentItem.created_at, ContentItem.created_at < parent.created_at):
                if child.parent_id:
                    child_parent = db.query(ContentItem).get(child.parent_id)
                    if child_parent.created_at - child_parent.started_at < parent.created_at - parent.started_at:
                        continue
                child.parent_id = parent.id
                db.flush()
