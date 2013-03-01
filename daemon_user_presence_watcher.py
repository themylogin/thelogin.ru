#!/usr/bin/python
# -*- coding: utf-8 -*-

import dateutil.parser
import re
import time

from db import db
from middleware.authorization.model import User, UserPresenceLog

syslog = open("/var/log/syslog") 

# Skip to the end of file
while syslog.readline():
    pass

while True:
    line = syslog.readline().strip()
    if not line:
        time.sleep(5)
        continue

    match = re.match(r"(.+) \w+ dhcpd: DHCPREQUEST .* from ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})", line)
    if match:
        date = dateutil.parser.parse(match.group(1))
        mac = match.group(2)

        for user in db.query(User):
            if user.settings and user.settings.get("MacAddress") == mac:
                presence = UserPresenceLog()
                presence.user_id = user.id
                presence.start = date
                presence.start_reason = "syslog: " + line
                db.add(presence)
                db.flush()
