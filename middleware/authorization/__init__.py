#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from werkzeug.exceptions import Forbidden

from config import config
from db import db
from model import User

def middleware(request):
    request.user = None
    if "u" in request.cookies:
        request.user = db.query(User).filter(User.token == request.cookies["u"]).first()
        if request.user:
            if datetime.now() > request.user.last_activity + config.user_inactivity_till_leave:
                request.user.last_visit = request.user.last_activity
            request.user.last_activity = datetime.now()
            db.flush()

    return request

def admin_action(action):    
    def decorated_action(self, request, **kwargs):
        if request.user.permissions & 0x1:
            return action(self, request, **kwargs)
        raise Forbidden()
    return decorated_action
