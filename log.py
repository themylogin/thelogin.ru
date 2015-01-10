#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from raven import Client

from config import config

client = Client(config.sentry_dsn)

logger = logging.getLogger("thelogin")
logger.setLevel(logging.DEBUG)
