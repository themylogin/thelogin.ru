#!/usr/bin/python
# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from config import config
    import logging, os
    config.__readonly__["debug"] = True
    config.__readonly__["url"] = "http://debug.thelogin.ru"
    config.__readonly__["cache"] = { "type" : "memory" }
    config.__readonly__["log"] = logging.FileHandler(os.path.join(os.path.dirname(__file__), "log_debug.txt"))

    from web import Application
    from werkzeug.serving import run_simple
    from werkzeug.contrib.profiler import ProfilerMiddleware
    run_simple("0.0.0.0", 6262, ProfilerMiddleware(Application(), open("profile.txt", "w")), use_debugger=True, use_reloader=True, threaded=True)
