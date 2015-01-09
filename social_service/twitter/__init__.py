#!/usr/bin/python
# -*- coding: utf-8 -*-

from cgi import parse_qsl

import oauth2
import twitter
import urllib
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.utils import redirect

class Twitter:	
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token_key = access_token_key
        self.access_token_secret = access_token_secret
        
        self.api = twitter.Api(consumer_key=self.consumer_key,
                               consumer_secret=self.consumer_secret,
                               access_token_key=self.access_token_key,
                               access_token_secret=self.access_token_secret)

    def oauth_initiate(self, callback_url):
        oauth_consumer  = oauth2.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        oauth_client    = oauth2.Client(oauth_consumer)

        resp, content   = oauth_client.request(twitter.REQUEST_TOKEN_URL, "POST", body=urllib.urlencode({ "oauth_callback" : callback_url }))
        if resp["status"] != "200":
            raise Exception("Unable to request token from Twitter: %s" % resp["status"])
        oauth_data = dict(parse_qsl(content))
        
        response = redirect(twitter.AUTHORIZATION_URL + "?oauth_token=" + oauth_data["oauth_token"])
        response.set_cookie("twitter_oauth", SecureCookie(oauth_data, self.consumer_secret).serialize(), httponly=True)
        return response

    def oauth_callback(self, request):
        if request.args.get("denied") is not None:
            return False

        try:
            oauth_data = SecureCookie.unserialize(request.cookies["twitter_oauth"], self.consumer_secret)
        except KeyError:
            return False

        oauth_token = oauth2.Token(oauth_data["oauth_token"], oauth_data["oauth_token_secret"])
        oauth_token.set_verifier(request.args.get("oauth_verifier"))

        oauth_consumer  = oauth2.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        oauth_client    = oauth2.Client(oauth_consumer, oauth_token)

        resp, content   = oauth_client.request(twitter.ACCESS_TOKEN_URL, "POST")
        if resp["status"] != "200":
            return False
        oauth_data = dict(parse_qsl(content))

        user_data = twitter.Api(consumer_key=self.consumer_key,
                                consumer_secret=self.consumer_secret,
                                access_token_key=oauth_data["oauth_token"],
                                access_token_secret=oauth_data["oauth_token_secret"]).VerifyCredentials().AsDict()
        return (user_data["id"], dict(user_data, **oauth_data))

    def is_trusted(self, service_data):
        api = twitter.Api(consumer_key=self.consumer_key,
                          consumer_secret=self.consumer_secret,
                          access_token_key=service_data["oauth_token"],
                          access_token_secret=service_data["oauth_token_secret"])
        print api.GetFriendIDs()
        return 19385503 in api.GetFriendIDs()

    def get_user_url(self, service_data):
        return "http://twitter.com/" + service_data["screen_name"]

    def get_user_name(self, service_data):
        return service_data["screen_name"]

    def get_user_avatar(self, service_data):
        return service_data["profile_image_url"]
