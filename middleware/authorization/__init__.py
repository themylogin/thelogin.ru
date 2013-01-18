#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config

def middleware(request):
    from db import db
    from model import User

    request.user = None
    if "u" in request.cookies:
        request.user = db.query(User).filter(User.token == request.cookies["u"]).first()
        if request.user:
            from datetime import datetime, timedelta
            if datetime.now() > request.user.last_activity + config.user_inactivity_till_leave:
                request.user.last_visit = request.user.last_activity
            request.user.last_activity = datetime.now()

    return request
