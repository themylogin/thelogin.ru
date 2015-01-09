#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import simplejson
from sqlalchemy import Column, Index, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, PickleType, String
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
    trusted             = Column(Boolean, default=False)
    trust_last_checked  = Column(DateTime(), default=None)

    external_id         = Index(service, service_id, unique=True)

class User(Base):
    __tablename__       = "user"

    id                  = Column(Integer, primary_key=True)
    token               = Column(String(length=32), unique=True)
    url_token           = Column(String(length=32), unique=True)
    last_visit          = Column(DateTime(), default=datetime.datetime.now)
    last_activity       = Column(DateTime(), default=datetime.datetime.now)
    default_identity_id = Column(Integer, ForeignKey("identity.id"))
    permissions         = Column(Integer, default=0)
    settings            = Column(PickleType(pickler=simplejson), default=dict)

    identities          = relationship("Identity", primaryjoin="Identity.user_id == User.id", backref="user")
    default_identity    = relationship("Identity", foreign_keys=default_identity_id, primaryjoin="Identity.id == User.default_identity_id")

    @property
    def trusted(self):
        return any(identity.trusted for identity in self.identities)


class Url(Base):
    __tablename__       = "url"

    id                  = Column(Integer, primary_key=True)
    encrypted_url       = Column(String(length=255), unique=True)
    decrypted_url       = Column(String(length=255))
    user_id             = Column(Integer, ForeignKey("user.id"))
    datetime            = Column(DateTime(), default=datetime.datetime.now)

    user                = relationship("User")


class Anonymous(Base):
    __tablename__       = "anonymous"

    id                  = Column(Integer, primary_key=True)
    token               = Column(String(length=32), unique=True)
    ip_addresses        = Column(PickleType(pickler=simplejson), default=dict)


class AnonymousUrlView(Base):
    __tablename__       = "anonymous_url_view"

    id                  = Column(Integer, primary_key=True)
    anonymous_id        = Column(Integer, ForeignKey("anonymous.id"))
    url_id              = Column(Integer, ForeignKey("url.id"))
    datetime            = Column(DateTime(), default=datetime.datetime.now)

    anonymous           = relationship("Anonymous")
    url                 = relationship("Url")
