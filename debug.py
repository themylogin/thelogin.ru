#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from werkzeug.contrib.profiler import ProfilerMiddleware
from werkzeug.serving import run_simple

from config import config
from web import Application

if __name__ == "__main__":
    config.__readonly__["debug"] = True
    config.__readonly__["url"] = config.url.replace("://", "://debug.")
    config.__readonly__["cache"] = { "type" : "memory" }
    config.__readonly__["log"] = logging.FileHandler(os.path.join(os.path.dirname(__file__), "log_debug.txt")) 

    application = Application()
    application = ProfilerMiddleware(application, open("profile.txt", "w"))

    run_simple("0.0.0.0", 6262, application, use_debugger=True, use_reloader=True, threaded=True)
