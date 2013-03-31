#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime        

from controller.content.model import ContentItem
from controller.content.type import abstract
from db import db
from local import local
from middleware.authorization.model import User
from social_service import all as all_social_service
from utils import urlencode

class Type(abstract.Type):
    def __init__(
        self,

        item_cases,
        item_mcases,

        title_renderer,
        image_directory
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.title_renderer = title_renderer
        self.image_directory = image_directory

    def get_provider(self):
        return None

    def get_formatter(self):
        return Formatter(self.title_renderer, self.image_directory)

    def get_editor(self):
        return None

class Formatter(abstract.Formatter):
    def __init__(self, title_renderer, image_directory):
        self.title_renderer = title_renderer
        self.image_directory = image_directory

    def is_context_dependent(self, content_item):
        return True

    def get_title(self, content_item):
        i_was_there = False
        if local.request.user:
            if local.request.user.permissions & ContentItem.permissions_PRIVATE:
                i_was_there = True
            else:
                in_or_out = db.query(ContentItem).filter(
                    ContentItem.type.startswith("guest_"),
                    ContentItem.type_key.startswith("user=%d," % local.request.user.id),
                    ContentItem.created_at < content_item.created_at
                ).order_by(-ContentItem.created_at).first()
                if in_or_out is not None and in_or_out.type == "guest_in":
                    i_was_there = True

        consumers = [db.query(User).get(1).default_identity]
        if i_was_there:
            processed_users = set()
            for in_ in db.query(ContentItem).filter(
                ContentItem.type == "guest_in",
                ContentItem.created_at < content_item.created_at
            ).order_by(-ContentItem.created_at):
                user_id = int(in_.type_key.split(",")[0].replace("user=", ""))
                if user_id in processed_users:
                    continue
                processed_users.add(user_id)

                out = db.query(ContentItem).filter(
                    ContentItem.type == "guest_out",
                    ContentItem.type_key.startswith("user=%d," % user_id),
                    ContentItem.created_at > in_.created_at,
                    ContentItem.created_at < content_item.created_at
                ).order_by(ContentItem.created_at).first()
                if out is None:
                    consumers.append(db.query(User).get(user_id).default_identity)
            consumers = [consumers[0]] + list(reversed(consumers[1:]))

        return self.title_renderer(consumers=consumers, content=content_item.data["title"])

    def get_image(self, content_item):
        return "/asset/img/content/type/content_consume/" + content_item.type + "/48x48.png"

    def get_description(self, content_item, url):
        return ""

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {
            "download"          :   datetime.fromtimestamp(content_item.data["download"]) if "download" in content_item.data else None,
            "start"             :   datetime.fromtimestamp(content_item.data["start"]) if "start" in content_item.data else None,
            "image_directory"   :   self.image_directory,
            "images"            :   map(urlencode, content_item.data.get("screenshots", [content_item.data["title"] + "." + str(i) + ".jpg" for i in range(1, 5)]))
        }

def create_title_renderer(alone, with_friends):
    def title_renderer(consumers, content):
        consumers = [u"<b>" + all_social_service[identity.service].get_user_name(identity.service_data) + u"</b>" for identity in consumers]

        if len(consumers) > 1:
            return with_friends % {
                "consumers" : u", ".join(consumers[:-1]) + u" и " + consumers[-1],
                "content"   : content,
            }
        else:
            return alone % {
                "consumer"  : consumers[0],
                "content"   : content,
            }

    return title_renderer
