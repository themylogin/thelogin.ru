#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, event, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session, scoped_session
from sqlalchemy.pool import Pool

from config import config
from local import local_manager

engine = create_engine(config.db, echo=config.debug)
def sessionmaker():
    session = create_session(engine)
    session._model_changes = {}
    return session
db = scoped_session(sessionmaker, local_manager.get_ident)

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()

Base = declarative_base()
