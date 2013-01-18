#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config

from beaker.cache import CacheManager
cache = CacheManager(**config.cache)
