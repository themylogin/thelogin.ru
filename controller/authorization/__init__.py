#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import dateutil.parser
from jinja2 import Markup
import random
import re
import string
from werkzeug.exceptions import Unauthorized
from werkzeug.routing import Rule
from werkzeug.utils import redirect

from config import config
from controller.abstract import Controller as Abstract
from controller.authorization.settings import all as all_settings
from controller.content.model import ContentItem
from db import db
from middleware.authorization.model import Identity, User
from utils import urlencode

class Controller(Abstract):
    def __init__(self, services):
        self.services = services

        self.export_function(globals(), "identity_url", lambda identity: self.services[identity.service].get_user_url(identity.service_data))
        self.export_function(globals(), "identity_name", lambda identity: self.services[identity.service].get_user_name(identity.service_data))
        self.export_function(globals(), "identity_avatar", lambda identity: self.services[identity.service].get_user_avatar(identity.service_data))

    def get_routes(self):
        return [
            Rule("/authorization/<any('" + "','".join(self.services.keys()) +"'):service>/initiate/",   endpoint="initiate"),            
            Rule("/authorization/<any('" + "','".join(self.services.keys()) +"'):service>/callback/",   endpoint="callback"),

            Rule("/authorization/usercp/",                  endpoint="usercp"),

            Rule("/authorization/set-default-identity/",    endpoint="set_default_identity"),
            Rule("/authorization/save-settings/",           endpoint="save_settings"),

            Rule("/authorization/logout-others/",   endpoint="logout_others"),
            Rule("/authorization/logout/",          endpoint="logout"),
        ]

    def execute_initiate(self, request, **kwargs):
        return self.services[kwargs["service"]].oauth_initiate(config.url + "/authorization/" + kwargs["service"] + "/callback/?from=" + urlencode(request.referrer or config.url))

    def execute_callback(self, request, **kwargs):
        result = self.services[kwargs["service"]].oauth_callback(request)
        if result:
            identity = db.query(Identity).filter(Identity.service == kwargs["service"], Identity.service_id == result[0]).first()
            if identity is None:
                identity = Identity()
                identity.service = kwargs["service"]
                identity.service_id = result[0]
                identity.service_data = result[1]
                db.add(identity)
                db.flush()
            if identity.user is None:
                if request.user is None:
                    identity.user = User()
                    # identity.user.default_identity = identity causes CircularDependencyError
                    identity.user.default_identity_id = identity.id
                    identity.user.token = "".join(random.choice(string.letters) for i in xrange(32))
                    db.add(identity.user)
                    db.flush()
                else:
                    identity.user = request.user
                    db.flush()
            else:
                if request.user is not None and request.user is not identity.user:
                    for other_identity in request.user.identities:
                        other_identity.user = identity.user
                    db.delete(request.user)
                    db.flush()

            response = redirect(request.args.get("from", "/"))
            response.set_cookie("u", identity.user.token, expires=datetime.now() + timedelta(days=365))
            return response
        else:
            raise Unauthorized()

    def execute_usercp(self, request):
        default_identity = None
        attached_identities = []
        available_services = []
        for service in sorted(self.services.keys()):
            identity_is_attached = False
            for identity in request.user.identities:
                if identity.service == service:
                    if identity == request.user.default_identity:
                        default_identity = identity
                    else:
                        attached_identities.append(identity)
                    identity_is_attached = True
                    break
            if not identity_is_attached:
                available_services.append(service)

        settings = [{
            "class" :   " ".join([cl.__name__ for cl in setting.__bases__]),
            "html"  :   Markup(setting.render(request.user)),
        } for setting in all_settings if setting.is_available(request.user)]

        macs = set()
        present_hardware = []
        for ip, lease in reversed(re.findall("lease([\d\s.]+){(.+?)}", open("/var/lib/dhcp/dhcpd.leases").read(), re.DOTALL)):
            ip              = ip.strip()
            start           = dateutil.parser.parse(re.search("starts.* ([0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", lease).group(1)) + config.timezone
            mac             = re.search("hardware ethernet ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})", lease).group(1)
            hostname        = re.search("client-hostname (.+);", lease)
            if hostname:
                hostname    = hostname.group(1).strip('"')
            else:
                hostname    = ""

            if config.owner_hardware(ip, mac):
                continue

            if datetime.now() - start > timedelta(days=1):
                continue

            if mac in macs:
                continue
            macs.add(mac)
            
            present_hardware.append({
                "start"     : start,
                "mac"       : mac,
                "hostname"  : hostname,
            })

        visit_history = []
        for user_in in db.query(ContentItem).filter(ContentItem.type == "guest_in",
                                                    ContentItem.type_key.startswith("user=%d," % (request.user.id,))).order_by(ContentItem.created_at.desc()):
            user_out = db.query(ContentItem).filter(ContentItem.type == "guest_out",
                                                    ContentItem.type_key.startswith("user=%d," % (request.user.id,)),
                                                    ContentItem.created_at >= user_in.created_at).order_by(ContentItem.created_at).first()
            visit_history.append((user_in, user_out))

        return self.render_to_response(request, "authorization/usercp.html", **{
            "default_identity"      : default_identity,
            "attached_identities"   : attached_identities,
            "available_services"    : available_services,
            "settings"              : settings,
            "present_hardware"      : present_hardware,
            "visit_history"         : visit_history,
            "breadcrumbs"           : [u"Подключенные сервисы"],
        })

    def execute_set_default_identity(self, request):
        target_identity_id = int(request.form["id"])
        for identity in request.user.identities:
            if identity.id == target_identity_id:
                request.user.default_identity = identity
                db.flush()
                break
        return redirect("/authorization/usercp/")

    def execute_save_settings(self, request):
        if request.user.settings is None:
            request.user.settings = {}
        for setting in all_settings:
            if setting.is_available(request.user):
                request.user.settings[setting.get_id()] = setting.accept_value(request.form)

        s = request.user.settings
        request.user.settings = None
        db.flush()
        request.user.settings = s
        db.flush()

        return redirect("/authorization/usercp/")

    def execute_logout_others(self, request):
        request.user.token = "".join(random.choice(string.letters) for i in xrange(32))
        db.flush()

        response = redirect(request.referrer or "/")
        response.set_cookie("u", request.user.token, expires=datetime.now() + timedelta(days=365))
        return response

    def execute_logout(self, request):
        response = redirect(request.referrer or "/")
        response.set_cookie("u", "")
        return response
