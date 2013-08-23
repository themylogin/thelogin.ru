#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import operator
import simplejson
from sqlalchemy import func
import time
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.routing import Rule
from werkzeug.wrappers import Response

from config import config
from controller.abstract import Controller as Abstract
from controller.content.model import ContentItem
from db import db
from middleware.authorization.model import User
from social_service import all as all_social_services

class Controller(Abstract):
    def get_routes(self):
        return [
            Rule("/smarthome_api/guest/find/",          endpoint="find_guest"),
            Rule("/smarthome_api/guest/present/",       endpoint="guest_list"),
            Rule("/smarthome_api/guest/in/<int:id>/",   endpoint="guest_in"),
            Rule("/smarthome_api/guest/out/<int:id>/",  endpoint="guest_out"),
        ]

    def decorate(action):
        def decorated_action(self, request, **kwargs):
            if request.remote_addr not in config.smarthome_api_addresses:
                raise Forbidden()
            return Response(simplejson.dumps(action(self, request, **kwargs)))
        return decorated_action

    @decorate
    def execute_find_guest(self, request):
        user = self.find_user(**request.args.to_dict(flat=True))
        if user is None:
            raise NotFound
        return self.format_guest(user)

    @decorate
    def execute_guest_list(self, request, **kwargs):
        guests = []
        for user in db.query(User):
            is_in = self.guest_is_in(user)
            if is_in:
                guests.append(self.format_guest(user))
        return sorted(guests, key=operator.itemgetter("came_at"))

    @decorate
    def execute_guest_in(self, request, id):
        user = db.query(User).get(id)
        if user is None:
            raise NotFound

        if self.guest_is_in(user):
            return False

        self.create_guest_record("guest_in", user)
        return True

    @decorate
    def execute_guest_out(self, request, id):
        user = db.query(User).get(id)
        if user is None:
            raise NotFound

        if not self.guest_is_in(user):
            return False

        self.create_guest_record("guest_out", user)
        return True

    def is_in(self, type, filter=True):
        last_in_or_out = db.query(ContentItem).filter(ContentItem.type.startswith(type) & filter).order_by(ContentItem.created_at.desc()).first()
        if last_in_or_out is None:
            return None
        if not last_in_or_out.type.endswith("_in"):
            return False
        return last_in_or_out

    def guest_is_in(self, user):
        return self.is_in("guest", ContentItem.type_key.startswith("user=%d," % (user.id,)))

    def create_record(self, **kwargs):
        record = ContentItem()
        record.type_key = int(time.time())
        record.created_at = datetime.now()
        record.permissions = ContentItem.permissions_PRIVATE
        record.data = {}
        for k, v in kwargs.items():
            setattr(record, k, v)
        db.add(record)
        db.flush()
        return record

    def create_guest_record(self, type, user):
        return self.create_record(
            type=type,
            type_key="user=%d, timestamp=%d" % (user.id, time.time()),
            data={"identity" : user.default_identity.id}
        )

    def find_user(self, **kwargs):
        if "id" in kwargs:
            return db.query(User).filter(User.id == int(kwargs["id"])).first()
        
        if "name" in kwargs:
            for user in db.query(User):
                if all_social_services[user.default_identity.service].get_user_name(user.default_identity.service_data) == kwargs["name"]:
                    return user

        if "mac" in kwargs:
            for user in db.query(User):
                if user.settings and user.settings.get("MacAddress") == kwargs["mac"]:
                    return user
        
        return None

    def format_guest(self, user):
        dct = {
            "id"            : user.id,
            "username"      : all_social_services[user.default_identity.service].get_user_name(user.default_identity.service_data),
            "avatar"        : all_social_services[user.default_identity.service].get_user_avatar(user.default_identity.service_data),
            "identities"    : dict([(identity.service, identity.service_data) for identity in user.identities]),
            "settings"      : user.settings,

            "visit_count"   : db.query(func.count(ContentItem.id)).filter(ContentItem.type == "guest_in", ContentItem.type_key.startswith("user=%d," % (user.id,))).scalar(),
        }

        is_in = self.guest_is_in(user)
        dct["is_in"] = bool(is_in)
        if dct["is_in"]:
            dct["came_at"] = is_in.created_at.isoformat()

        last_visit = db.query(func.max(ContentItem.created_at)).filter(ContentItem.type == "guest_out", ContentItem.type_key.startswith("user=%d," % (user.id,))).scalar()
        if last_visit:
            dct["last_visit"] = last_visit.isoformat()

        return dct
