#!/usr/bin/python
# -*- coding: utf-8 -*-

class Facebook:	
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def oauth_initiate(self, callback_url):
        import facebook
        from werkzeug.utils import redirect
        from werkzeug.contrib.securecookie import SecureCookie        
        response = redirect(facebook.auth_url(self.client_id, callback_url))     
        response.set_cookie("facebook_oauth", SecureCookie({ "callback_url" : callback_url }, self.client_secret).serialize(), httponly=True)
        return response

    def oauth_callback(self, request):
        try:
            from werkzeug.contrib.securecookie import SecureCookie
            callback_url = SecureCookie.unserialize(request.cookies["facebook_oauth"], self.client_secret)["callback_url"]
        except KeyError:
            return False

        import facebook
        access_token = facebook.get_access_token_from_code(request.args.get("code"), callback_url, self.client_id, self.client_secret)["access_token"]
        user = facebook.GraphAPI(access_token).get_object("me")
        
        return (int(user["id"]), dict(user, access_token=access_token))

    def get_user_url(self, service_data):
        return service_data["link"]

    def get_user_name(self, service_data):
        return service_data["name"]

    def get_user_avatar(self, service_data):
        return "https://graph.facebook.com/" + service_data["id"] + "/picture"
