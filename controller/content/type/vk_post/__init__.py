#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import re
import simplejson
import urllib
import urllib2

from controller.content.type import abstract
from kv import storage as kv_storage

class Type(abstract.Type):
    def __init__(
        self,

        client_id, client_secret,
        user_id, user_name, user_avatar,
        
        item_cases      = (u"пост вконтакте",   u"поста вконтакте",     u"посту вконтакте",     u"пост вконтакте",  u"постом вконтакте",    u"посте вконтакте"),
        item_mcases     = (u"посты вконтакте",  u"постов вконтакте",    u"постам вконтакте",    u"посты вконтакте", u"постами вконтакте",   u"постах вконтакте"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.client_id = client_id
        self.client_secret = client_secret

        self.user_id = user_id
        self.user_name = user_name
        self.user_avatar = user_avatar

    def get_provider(self):
        return Provider(self.user_id)

    def get_formatter(self):
        return Formatter(self.user_id, self.user_name, self.user_avatar)

    def get_editor(self):
        return None

class Provider(abstract.Provider):
    def __init__(self, user_id):
        self.user_id = user_id

    def provide(self):
        for status in simplejson.loads(urllib2.urlopen(urllib2.Request("https://api.vk.com/method/wall.get?owner_id=%(user_id)s&filter=owner&count=100" % {
            "user_id" : self.user_id,
        })).read())["response"][1:]:
            status_created_at = datetime.fromtimestamp(status["date"])

            def vk_owner(status):
                if "copy_commenter_id" in status:
                    owner_id = status["copy_commenter_id"]
                elif "copy_owner_id" in status:
                    owner_id = status["copy_owner_id"]

                key_prefix = str(owner_id) + "-" + status_created_at.strftime("%Y-%m-%d")

                if owner_id > 0:
                    user = simplejson.loads(urllib2.urlopen(urllib2.Request("https://api.vk.com/method/users.get?uids=%(user_id)s&fields=uid,first_name,last_name,screen_name,photo&lang=en" % {
                        "user_id" : owner_id
                    })).read())["response"][0]
                    return [
                        (key_prefix + "-photo", user["photo"]),
                        (key_prefix + "-title", user["first_name"] + " " + user["last_name"]),
                        (key_prefix + "-url",   "http://vk.com/" + user["screen_name"]),
                    ]
                else:
                    group = simplejson.loads(urllib2.urlopen(urllib2.Request("https://api.vk.com/method/groups.getById?gid=%(group_id)s" % {
                        "group_id" : -owner_id
                    })).read())["response"][0]
                    return [
                        (key_prefix + "-photo", group["photo"]),
                        (key_prefix + "-title", group["name"]),
                        (key_prefix + "-url",   "http://vk.com/" + group["screen_name"]),
                    ]

            yield self.provider_item(
                id          =   status["id"],
                created_at  =   status_created_at,
                data        =   status,
                kv          =   { "vk owner" : lambda: vk_owner(status) } if "copy_owner_id" in status or "copy_commenter_id" in status else {},
            )

class Formatter(abstract.Formatter):
    def __init__(self, user_id, user_name, user_avatar):
        self.user_id = user_id
        self.user_name = user_name
        self.user_avatar = user_avatar

    def get_title(self, content_item):
        repost = self.get_repost(content_item)
        if repost:
            owner = repost["owner"]
        else:
            owner = {
                "photo" : self.user_avatar,
                "title" : self.user_name,
                "url"   : "http://vk.com/id" + str(self.user_id),
            }

        return """<a href="%(url)s">%(title)s</a>""" % owner

    def get_image(self, content_item):        
        repost = self.get_repost(content_item)
        if repost:
            return repost["owner"]["photo"]
        return self.user_avatar

    def get_description(self, content_item, url):        
        text = content_item.data["text"]

        repost = self.get_repost(content_item)
        if repost:
            text += repost["text"]

        text = re.sub(r"\[([^\]]+)\|([^\]]+)\]", r'<a href="http://vk.com/\1">\2</a>', text)
        return text

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {
            "is_copy"       : self.get_repost(content_item) is not None,
            "url"           : "http://vk.com/wall" + str(self.user_id) + "_" + str(content_item.data["id"]),
            "attachments"   : content_item.data.get("attachments", None),
        }

    #
    def get_repost(self, content_item):
        if "copy_commenter_id" in content_item.data:
            owner_id = content_item.data["copy_commenter_id"]
        elif "copy_owner_id" in content_item.data:            
            owner_id = content_item.data["copy_owner_id"]
        else:
            return None

        key_prefix = str(owner_id) + "-" + content_item.created_at.strftime("%Y-%m-%d")

        return {
            "owner" : {
                "photo" : kv_storage["vk owner"][key_prefix + "-photo"], 
                "title" : kv_storage["vk owner"][key_prefix + "-title"],
                "url"   : kv_storage["vk owner"][key_prefix + "-url"],
            },
            "text"  : content_item.data["copy_text"] if "copy_text" in content_item.data else "",
        }
