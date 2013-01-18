#!/usr/bin/python
import sys
sys.path.insert(0, "/home/themylogin/www/apps/thelogin62a")

from web import Application
from flup.server.fcgi import WSGIServer
WSGIServer(Application()).run()
