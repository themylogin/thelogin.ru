#!/usr/bin/python
# -*- coding: utf-8 -*-

from kv.engine.abstract import Engine as Abstract
from db import db

class Engine(Abstract):
    def get(self, directory, key):
        value = db.query(KV.value).filter_by(directory=directory, key=key).scalar()
        if value is None:
            raise KeyError(key)
        return value

    def set(self, directory, key, value):
        kv = db.query(KV).filter_by(directory=directory, key=key).first()
        if kv is None:
            kv = KV()
            kv.directory = directory
            kv.key = key
            db.add(kv)

        kv.value = value
        db.flush()

    def delete(self, directory, key):
        kv = db.query(KV).filter_by(directory=directory, key=key).first()
        if kv is None:
            raise KeyError
        db.delete(kv)
        db.flush()

    def all(self, directory):
        return db.query(KV.key, KV.value).filter_by(directory=directory).all()

from sqlalchemy import Column, Index
from sqlalchemy import Integer, String, Text

from db import Base

class KV(Base):
    __tablename__   = 'kv'

    id              = Column(Integer, primary_key=True)
    directory       = Column(String(length=32))
    key             = Column(String(length=255))
    value           = Column(Text())

    directory_key   = Index(directory, key, unique=True)
