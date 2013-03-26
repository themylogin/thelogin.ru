#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import operator
import simplejson
import time
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.routing import Rule
from werkzeug.wrappers import Response

from config import config
from controller.abstract import Controller as Abstract
from controller.content.model import ContentItem
from db import db
from middleware.authorization.model import User
from mq import mq_channel
from social_service import all as all_social_services

class Controller(Abstract):
    def __init__(self):
        mq_channel.exchange_declare(exchange="thelogin_smarthome_api", type="fanout")

    def get_routes(self):
        return [
            Rule("/smarthome_api/owner/in/",            endpoint="owner_in"),
            Rule("/smarthome_api/owner/out/",           endpoint="owner_out"),

            Rule("/smarthome_api/guests/",              endpoint="guests"),
            Rule("/smarthome_api/guest/in/",            endpoint="guest_in"),
            Rule("/smarthome_api/guest/out/",           endpoint="guest_out"),
        ]

    def decorate(action):
        def decorated_action(self, request, **kwargs):
            if request.remote_addr not in config.smarthome_api_addresses:
                raise Forbidden()
            return Response(simplejson.dumps(action(self, request, **kwargs)))
        return decorated_action

    @decorate
    def execute_owner_in(self, request, **kwargs):
        if self.is_in("owner"):
            return False

        self.create_record(type="owner_in")
        return True

    @decorate
    def execute_owner_out(self, request, **kwargs):
        if not self.is_in("owner"):
            return False

        self.create_record(type="owner_out")
        return True

    @decorate
    def execute_guests(self, request, **kwargs):
        guests = []
        for user in db.query(User):
            is_in = self.guest_is_in(user)
            if is_in:
                guests.append((is_in.created_at, {
                    "id"            : user.id,
                    "username"      : all_social_services[user.default_identity.service].get_user_name(user.default_identity.service_data),
                    "avatar"        : all_social_services[user.default_identity.service].get_user_avatar(user.default_identity.service_data),
                    "identities"    : dict([(identity.service, identity.service_data) for identity in user.identities]),
                }))
        return map(operator.itemgetter(1), sorted(guests, key=operator.itemgetter(0)))

    @decorate
    def execute_guest_in(self, request, **kwargs):
        user = self.find_guest(**request.args.to_dict(flat=True))
        if user is None:
            raise NotFound

        if self.guest_is_in(user):
            return False

        self.create_guest_record("guest_in", user)
        mq_channel.basic_publish(exchange="thelogin_smarthome_api", routing_key="", body="guests_updated")
        return True

    @decorate
    def execute_guest_out(self, request, **kwargs):
        user = self.find_guest(**request.args.to_dict(flat=True))
        if user is None:
            raise NotFound

        if not self.guest_is_in(user):
            return False

        self.create_guest_record("guest_out", user)
        mq_channel.basic_publish(exchange="thelogin_smarthome_api", routing_key="", body="guests_updated")
        return True

    def is_in(self, type, filter=True):
        last_in_or_out = db.query(ContentItem).filter(ContentItem.type.startswith(type) & filter).order_by(-ContentItem.created_at).first()
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

    def find_guest(self, **kwargs):
        if "id" in kwargs:
            return db.query(User).filter(User.id == int(kwargs["id"])).first()
        elif "mac" in kwargs:
            for user in db.query(User):
                if user.settings and user.settings.get("MacAddress") == kwargs["mac"]:
                    return user
        return None
