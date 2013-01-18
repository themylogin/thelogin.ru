#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Index, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, PickleType, String, Text

from sqlalchemy.orm import relationship

import datetime
import simplejson

from db import Base
from middleware.authorization.model import Identity

ContentItemTag = Table("content_item_tag", Base.metadata,
    Column("content_item_id",   Integer, ForeignKey("content_item.id")),
    Column("tag_id",            Integer, ForeignKey("tag.id"))
)

class ContentItem(Base):
    __tablename__       = "content_item"

    id                  = Column(Integer, primary_key=True)
    type                = Column(String(length=32))
    type_key            = Column(String(length=255))
    created_at          = Column(DateTime())
    public              = Column(Boolean())
    data                = Column(PickleType(pickler=simplejson))

    type__type_key      = Index(type, type_key, unique=True)
    type__created_at    = Index(type, created_at)

    tags                = relationship("Tag", secondary=ContentItemTag)
    comments            = relationship("Comment", primaryjoin="Comment.content_item_id == ContentItem.id", order_by="Comment.created_at", backref="content_item")

class Tag(Base):
    __tablename__       = "tag"

    id                  = Column(Integer, primary_key=True)
    url                 = Column(String(length=255), unique=True)
    title               = Column(String(length=255))

    content_items       = relationship("ContentItem", secondary=ContentItemTag)

class Comment(Base):
    __tablename__       = "comment"

    id                  = Column(Integer, primary_key=True)
    content_item_id     = Column(Integer, ForeignKey("content_item.id"))
    created_at          = Column(DateTime(), default=datetime.datetime.now)
    identity_id         = Column(Integer, ForeignKey("identity.id"))
    text                = Column(Text)
    analytics           = Column(PickleType(pickler=simplejson))

    identity            = relationship("Identity", foreign_keys=identity_id, primaryjoin="Identity.id == Comment.identity_id")
