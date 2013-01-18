#!/usr/bin/python
# -*- coding: utf-8 -*-

class Controller:
    def export_function(self, globals, function_name, function):        
        import sys
        setattr(sys.modules[globals["__name__"]], function_name, function)

        from template import jinja
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
        from werkzeug.wrappers import Response
        return Response(self.render_template(request, template_name, **context), mimetype="text/html")

    def render_template(self, request, template_name, **context):
        from config import config
        from assets import assets
        from template import jinja
        return jinja.get_or_select_template(template_name).render(dict({
            "config"        :   config,
            "assets"        :   assets,
            "request"       :   request,
        }, **context))
