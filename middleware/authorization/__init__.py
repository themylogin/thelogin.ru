#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import random
import string
from werkzeug.exceptions import Forbidden

from config import config
from db import db
from model import Anonymous, User

def middleware(request):
    request.user = None
    if "u" in request.cookies:
        request.user = db.query(User).filter(User.token == request.cookies["u"]).first()
        if request.user:
            if datetime.now() > request.user.last_activity + config.user_inactivity_till_leave:
                request.user.last_visit = request.user.last_activity
            request.user.last_activity = datetime.now()
            db.flush()

    request.anonymous = None
    if request.remote_addr != "127.0.0.1":
        if request.user is None:
            if "a" in request.cookies:
                request.anonymous = db.query(Anonymous).filter(Anonymous.token == request.cookies["a"]).first()

            if request.anonymous is None:
                request.anonymous = Anonymous()
                request.anonymous.token = "".join(random.choice(string.letters + string.digits + string.punctuation)
                                                  for i in xrange(32))
                db.add(request.anonymous)
                db.flush()

            if request.remote_addr not in request.anonymous.ip_addresses:
                request.anonymous.ip_addresses = {a: True for a in request.anonymous.ip_addresses.keys()}
                request.anonymous.ip_addresses[request.remote_addr] = True
                db.flush()

    return request

def admin_action(action):    
    def decorated_action(self, request, **kwargs):
        if request.user.permissions & 0x1:
            return action(self, request, **kwargs)
        raise Forbidden()
    return decorated_action
