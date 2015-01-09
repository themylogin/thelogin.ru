#!/usr/bin/python
# -*- coding: utf-8 -*-

from binascii import hexlify
from Crypto.Cipher import AES
from functools import partial
import re
import sys
import urlparse
from werkzeug.wrappers import Response

from assets import assets
from config import config
from template import jinja

LOCAL_DOMAIN = urlparse.urlparse(config.url).netloc

class Controller(object):
    def export_function(self, globals, function_name, function):                
        setattr(sys.modules[globals["__name__"]], function_name, function)
        jinja.filters[function_name] = function

    def get_routes(self):
        raise NotImplementedError("""
            Controller should have routes. E.g.:

            def get_routes(self):
                from werkzeug.routing import Rule
                return [
                    Rule("/controller/action1",         endpoint="action1"),
                    Rule("/controller/action2/<arg1>",  endpoint="action2"),
                ]
        """)

    def render_to_response(self, request, template_name, **context):
        html = self.render_template(request, template_name, **context)
        if request.user is not None and request.user.permissions == 0:
            html = re.sub('(data-url|href)="(.+?)"', partial(self._hide_url_callback, request.user.url_token),
                          html.encode("utf-8")).decode("utf-8")
        return Response(html, mimetype="text/html")

    def render_template(self, request, template_name, **context):        
        return jinja.get_or_select_template(template_name).render(dict({
            "config"        :   config,
            "assets"        :   assets,
            "request"       :   request,
        }, **context))

    def _hide_url_callback(self, url_token, m):
        if not hasattr(self, "_cipher"):
            self._cipher = AES.new(url_token)

        url = m.group(2)
        if "#" in url:
            url, anchor = url.split("#", 1)
        else:
            anchor = None
        if url != "":
            result = urlparse.urlparse(url)
            if ((result.netloc == "" or result.netloc.endswith(LOCAL_DOMAIN)) and
                    not any(result.path.startswith(p) for p in ("/asset", "/data", "/images", "/favicon.ico"))):
                if result.path == "":
                    url_prefix = ""
                else:
                    url_prefix = url.split(result.path)[0]
                url = url[len(url_prefix):]
                url = hexlify(self._cipher.encrypt(self._pad(url)))
                url = url_prefix + "/private/%s" % url
        if anchor is not None:
            url += "#%s" % anchor
        return '%s="%s"' % (m.group(1), url)

    def _pad(self, s):
        BLOCK_SIZE = 32
        return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * "@"
