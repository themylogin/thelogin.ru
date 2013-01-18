#!/usr/bin/python
# -*- coding: utf-8 -*-

from kv.storage import Storage
from kv.engine.sql import Engine

storage = Storage(Engine())
