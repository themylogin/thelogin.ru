#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import func

from db import db
from sqlalchemy.orm import joinedload
from controller.content.model import ContentItem, Comment
from controller.content import process_content_item

def block(request, limit=10):
    return {
        "last_comments" : [
            {
                "comment"       : db.query(Comment).options(joinedload("content_item")).filter(Comment.content_item_id == content_item_id).order_by(Comment.created_at.desc()).first(),
                "content_item"  : process_content_item(db.query(ContentItem).get(content_item_id)),

                "count_new"     : db.query(func.count(Comment)).filter(Comment.content_item_id == content_item_id, Comment.created_at > request.user.last_visit).scalar() if request.user else 0,
                "new_index"     : (db.query(func.count(Comment)).filter(Comment.content_item_id == content_item_id, Comment.created_at <= request.user.last_visit).scalar() if request.user else 0) + 1,
            }
            for content_item_id, in db.query(Comment.content_item_id).group_by(Comment.content_item_id).order_by(-func.max(Comment.created_at))[:limit]
        ],
    }
