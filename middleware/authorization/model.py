#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import simplejson
from sqlalchemy import Column, Index, ForeignKey
from sqlalchemy import DateTime, Integer, PickleType, String
from sqlalchemy.orm import relationship

from db import Base

class Identity(Base):
    __tablename__       = "identity"

    id                  = Column(Integer, primary_key=True)
    user_id             = Column(Integer, ForeignKey("user.id"))
    datetime            = Column(DateTime(), default=datetime.datetime.now)
    service             = Column(String(length=32))
    service_id          = Column(Integer())
    service_data        = Column(PickleType(pickler=simplejson))

    external_id         = Index(service, service_id, unique=True)

class User(Base):
    __tablename__       = "user"

    id                  = Column(Integer, primary_key=True)
    token               = Column(String(length=32), unique=True)
    last_visit          = Column(DateTime(), default=datetime.datetime.now)
    last_activity       = Column(DateTime(), default=datetime.datetime.now)
    default_identity_id = Column(Integer, ForeignKey("identity.id"))
    permissions         = Column(Integer, default=0)
    settings            = Column(PickleType(pickler=simplejson), default={})

    identities          = relationship("Identity", primaryjoin="Identity.user_id == User.id", backref="user")
    default_identity    = relationship("Identity", foreign_keys=default_identity_id, primaryjoin="Identity.id == User.default_identity_id")
