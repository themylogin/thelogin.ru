#!/usr/bin/python
# -*- coding: utf-8 -*-

from beaker.cache import CacheManager

from config import config

cache = CacheManager(**config.cache)
