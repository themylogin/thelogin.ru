#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloggy.werkzeug_client import WerkzeugLoggingHandler
import logging
import os.path
import sys

from local import local

logger = logging.getLogger("thelogin")
logger.setLevel(logging.DEBUG)

logger.addHandler(WerkzeugLoggingHandler(request_provider=lambda: getattr(local, "request", None)))
