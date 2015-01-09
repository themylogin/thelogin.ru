#!/usr/bin/python
# -*- coding: utf-8 -*-

from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
from datetime import datetime, timedelta
from functools import partial
import re
from urlparse import urlparse
from werkzeug.exceptions import HTTPException, Forbidden, InternalServerError
from werkzeug.routing import EndpointPrefix, Map
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

from config import config
from controller import all as controllers
from db import db
from local import local, local_manager
from log import logger
from middleware import all as all_middleware
from middleware.authorization.model import AnonymousUrlView, Url

# WSGI application
class Application:
    def __init__(self):
        self.controllers = controllers
        self.url_map = Map([EndpointPrefix("{0}/".format(i), self.controllers[i].get_routes()) for i in range(0, len(self.controllers))])

        self.local_domain = urlparse(config.url).netloc

    def __call__(self, environ, start_response):
        def app(environ, start_response):
            request = Request(environ)

            local.request = request

            if config.debug:
                response = self.process_request(request)
            else:
                try:
                    response = self.process_request(request)
                except Forbidden:
                    response = self.controllers[0].render_to_response(request, "private.html")
                except HTTPException, e:
                    response = e
                except Exception, e:               
                    logger.exception("An unhandled exception occurred during the execution of the current web request")
                    response = InternalServerError()
            return response(environ, start_response)

        return ClosingIterator(local_manager.make_middleware(app)(environ, start_response), db.remove)

    def process_request(self, request):
        for middleware in all_middleware:
            request = middleware(request)

        if request.environ["PATH_INFO"].startswith("/private/"):
            path_info = request.environ["PATH_INFO"]
            path_info = path_info[len("/private/"):]
            if not (request.user is None or not request.user.trusted):
                path_info_encrypted = path_info
                path_info = AES.new(request.user.url_token).decrypt(unhexlify(path_info)).rstrip("@")

                url = db.query(Url).filter(Url.encrypted_url == path_info_encrypted).first()
                if url is None:
                    url = Url()
                    url.encrypted_url = path_info_encrypted
                    url.decrypted_url = path_info
                    url.user = request.user
                    db.add(url)
            else:
                url = db.query(Url).filter(Url.encrypted_url == path_info).first()
                if url is None:
                    raise Forbidden()
                if not any(url.decrypted_url.startswith(p)
                           for p in ("/blog/post/", "/gallery/view/", "/video/view/",
                                     "/chatlogs/view/", "/library/view/", "/shop/view/")):
                    raise Forbidden()

                auv = db.query(AnonymousUrlView).filter(AnonymousUrlView.anonymous == request.anonymous,
                                                        AnonymousUrlView.url == url).first()
                if auv is None:
                    auv = AnonymousUrlView()
                    auv.anonymous = request.anonymous
                    auv.url = url
                    db.add(auv)
                    db.flush()

                path_info = url.decrypted_url

            request.environ["PATH_INFO"] = path_info

            request = Request(request.environ)

            local.request = request

            for middleware in all_middleware:
                request = middleware(request)
        else:
            if request.user is None or not request.user.trusted:
                if not any(request.environ["PATH_INFO"].startswith(p)
                           for p in ("/authorization/", "/content/post-comment/")):
                    raise Forbidden()

        endpoint, values = self.url_map.bind_to_environ(request.environ, server_name=urlparse(config.url).netloc.split(":")[0]).match()
        controller, controller_endpoint = endpoint.split("/", 1)

        controller = self.controllers[int(controller)]
        controller_method = "execute_{0}".format(controller_endpoint)

        response = getattr(controller, controller_method)(request, **values)

        if request.anonymous is not None:
            response.set_cookie("a", request.anonymous.token, expires=datetime.now() + timedelta(days=365))

        if request.user is not None and request.user.permissions == 0:
            if isinstance(response.data, str):
                response.data = re.sub('(data-url|href)="(.+?)"',
                                       partial(self._hide_url_callback, request.user.url_token),
                                       response.data)

            if "Location" in response.headers:
                response.headers["Location"] = self._encrypt_url(request.user.url_token,
                                                                 response.headers["Location"])

        if request.anonymous:
            if "Location" in response.headers:
                parts = self._encrypt_url_parts(response.headers["Location"])
                if parts:
                    url_prefix, url, anchor = parts
                    url_view = db.query(AnonymousUrlView).\
                                  join(Url).\
                                  filter(AnonymousUrlView.anonymous == request.anonymous,
                                         Url.decrypted_url == url).\
                                  first()
                    if url_view:
                        response.headers["Location"] = self._build_url(url_prefix, url_view.url.encrypted_url, anchor)


        return response

    def _hide_url_callback(self, url_token, m):
        return '%s="%s"' % (m.group(1), self._encrypt_url(url_token, m.group(2)))

    def _encrypt_url(self, url_token, url):
        cipher = AES.new(url_token)

        parts = self._encrypt_url_parts(url)
        if parts:
            url_prefix, url, anchor = parts
            url = self._build_url(url_prefix, hexlify(cipher.encrypt(self._pad(url))), anchor)

        return url

    def _encrypt_url_parts(self, url):
        if "#" in url:
            url, anchor = url.split("#", 1)
        else:
            anchor = None
        if url != "":
            result = urlparse(url)
            if ((result.netloc == "" or result.netloc.endswith(self.local_domain)) and
                    not any(result.path.startswith(p) for p in ("/asset", "/data", "/images", "/favicon.ico"))):
                if result.path == "":
                    url_prefix = ""
                else:
                    url_prefix = url.split(result.path)[0]

                return url_prefix, url[len(url_prefix):], anchor

        return None

    def _build_url(self, url_prefix, encrypted_url, anchor):
        url = url_prefix + "/private/%s" % encrypted_url
        if anchor is not None:
            url += "#%s" % anchor
        return url

    def _pad(self, s):
        BLOCK_SIZE = 32
        return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * "@"
