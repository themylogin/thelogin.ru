#!/usr/bin/python
# -*- coding: utf-8 -*-

# http://werkzeug.pocoo.org/docs/local/
from werkzeug import Local, LocalManager

local = Local()
local_manager = LocalManager([local]) 
