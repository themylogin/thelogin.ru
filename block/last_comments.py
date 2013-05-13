#!/usr/bin/python
# -*- coding: utf-8 -*-

def block(request, limit=10):
    from db import db
    from sqlalchemy.orm import joinedload
    from controller.content.model import Comment
    from controller.content import process_content_item

    from sqlalchemy import func
    return {
        "last_comments" : [
            {
                "comment"       : db.query(Comment).options(joinedload("content_item")).filter(Comment.content_item == comment.content_item).order_by(Comment.created_at.desc()).first(),
                "content_item"  : process_content_item(comment.content_item),

                "count_new"     : db.query(func.count(Comment)).filter(Comment.content_item == comment.content_item, Comment.created_at > request.user.last_visit).scalar() if request.user else 0,
                "new_index"     : (db.query(func.count(Comment)).filter(Comment.content_item == comment.content_item, Comment.created_at <= request.user.last_visit).scalar() if request.user else 0) + 1,
            }
            for comment in db.query(Comment).group_by(Comment.content_item_id).order_by(-func.max(Comment.created_at))[:limit]
        ],
    }
