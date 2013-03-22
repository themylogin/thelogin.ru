#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "loggy"))
from cloggy.werkzeug_client import WerkzeugLoggingHandler

from local import local

logger = logging.getLogger("thelogin")
logger.setLevel(logging.DEBUG)

logger.addHandler(WerkzeugLoggingHandler(request_provider=lambda: getattr(local, "request", None)))
