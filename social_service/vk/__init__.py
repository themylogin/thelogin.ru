#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson
import urllib2
from werkzeug.utils import redirect

from utils import urlencode

class Vk:	
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def oauth_initiate(self, callback_url):
        return redirect("http://api.vk.com/oauth/authorize?client_id=" + self.client_id + "&redirect_uri=" + urlencode(callback_url) + "&display=page")

    def oauth_callback(self, request):
        if request.args.get("error") is not None:
            return False

        # TODO: import vkontakte
        access_token = simplejson.loads(urllib2.urlopen(urllib2.Request("https://api.vkontakte.ru/oauth/access_token?client_id=" + self.client_id + "&client_secret=" + self.client_secret + "&code=" + urlencode(request.args.get("code")))).read())
        user = simplejson.loads(urllib2.urlopen(urllib2.Request("https://api.vkontakte.ru/method/getProfiles?uid=" + str(access_token["user_id"]) + "&access_token=" + access_token["access_token"] + "&fields=uid,first_name,last_name,nickname,screen_name,photo")).read())["response"][0]
        
        return (int(user["uid"]), dict(user, access_token=access_token["access_token"]))

    def get_user_url(self, service_data):
        return "http://vk.com/" + service_data["screen_name"]

    def get_user_name(self, service_data):
        return service_data["first_name"] + " " + service_data["last_name"]

    def get_user_avatar(self, service_data):
        return service_data["photo"]
