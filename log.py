#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config
import logging, os.path

logger = logging.getLogger("thelogin")
logger.setLevel(logging.DEBUG)

handler = config.log
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%b %d %H:%M:%S"))
logger.addHandler(handler) 
