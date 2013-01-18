#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config
from local import local_manager

from sqlalchemy import create_engine
from sqlalchemy.orm import create_session, scoped_session

db = scoped_session(lambda: create_session(create_engine(config.db, echo=config.debug)), local_manager.get_ident)

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
