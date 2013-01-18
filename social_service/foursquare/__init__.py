#!/usr/bin/python
# -*- coding: utf-8 -*-

# wget http://curl.haxx.se/ca/cacert.pem -O /usr/local/lib/python2.6/dist-packages/httplib2-0.7.2-py2.6.egg/httplib2/cacerts.txt

class Foursquare:	
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def oauth_initiate(self, callback_url):
        import foursquare
        from werkzeug.utils import redirect
        from werkzeug.contrib.securecookie import SecureCookie        
        response = redirect(foursquare.Foursquare(client_id=self.client_id, client_secret=self.client_secret, redirect_uri=callback_url).oauth.auth_url())        
        response.set_cookie("foursquare_oauth", SecureCookie({ "callback_url" : callback_url }, self.client_secret).serialize(), httponly=True)
        return response

    def oauth_callback(self, request):
        try:
            from werkzeug.contrib.securecookie import SecureCookie
            callback_url = SecureCookie.unserialize(request.cookies["foursquare_oauth"], self.client_secret)["callback_url"]
        except KeyError:
            return False

        import foursquare
        client = foursquare.Foursquare(client_id=self.client_id, client_secret=self.client_secret, redirect_uri=callback_url)
        access_token = client.oauth.get_token(request.args.get("code"))
        client.set_access_token(access_token)
        user = client.users()
        
        return (int(user["user"]["id"]), dict(user, access_token=access_token))

    def get_user_url(self, service_data):
        return "http://foursquare.com/user/" + service_data["user"]["id"]

    def get_user_name(self, service_data):
        return service_data["user"]["firstName"] + " " + service_data["user"]["lastName"]

    def get_user_avatar(self, service_data):
        return service_data["user"]["photo"]
