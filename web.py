#!/usr/bin/python
# -*- coding: utf-8 -*-

from urlparse import urlparse
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.routing import EndpointPrefix, Map
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

from config import config
from controller import all as controllers
from db import db
from local import local, local_manager
from log import logger
from middleware import all as all_middleware

# WSGI application
class Application:
    def __init__(self):
        self.controllers = controllers
        self.url_map = Map([EndpointPrefix("{0}/".format(i), self.controllers[i].get_routes()) for i in range(0, len(self.controllers))])

    def __call__(self, environ, start_response):
        def app(environ, start_response):
            request = Request(environ)

            local.request = request

            if config.debug:
                response = self.process_request(request)
            else:
                try:
                    response = self.process_request(request)
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

        endpoint, values = self.url_map.bind_to_environ(request.environ, server_name=urlparse(config.url).netloc.split(":")[0]).match()
        controller, controller_endpoint = endpoint.split("/", 1)

        controller = self.controllers[int(controller)]
        controller_method = "execute_{0}".format(controller_endpoint)

        response = getattr(controller, controller_method)(request, **values)
        return response
