#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import dateutil.parser
from jinja2 import ChoiceLoader, contextfunction, Environment, FileSystemLoader, Markup
import inspect
import os
import sys
import urllib

from cache import cache
from config import config

if config.debug:
    auto_reload = True
    bytecode_cache = None
else:
    auto_reload = False    
    bytecode_cache = None

jinja = Environment(
    loader          =   FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape      =   True,
    auto_reload     =   auto_reload,
    bytecode_cache  =   bytecode_cache
)

jinja.filters["date"]               = config.format_date
jinja.filters["time"]               = config.format_time
jinja.filters["datetime"]           = config.format_datetime
jinja.filters["datetime_relative"]  = config.format_datetime_relative
jinja.filters["date_period"]        = config.format_date_period

jinja.filters["datetime_from_int"]          = lambda int: datetime.fromtimestamp(int)
jinja.filters["datetime_from_str"]          = lambda str: dateutil.parser.parse(str) + config.timezone
jinja.filters["datetime_from_str_local"]    = lambda str: dateutil.parser.parse(str)
       
jinja.filters["decline"] = lambda number, *args: args[0].format(number) if number % 10 == 1 and number % 100 != 11 else args[1].format(number) if number % 10 in [2, 3, 4] and (number % 100 < 10 or number % 100 > 20) else args[2].format(number)

jinja.filters["urlencode_plus"] = lambda s: urllib.quote_plus(s.encode("utf-8"))

jinja.filters["time_duration"]  = lambda seconds: "%(h)2d:%(m)02d:%(s)02d" % { "h" : int(seconds / 60 / 60), "m" : int(seconds / 60 % 60), "s" : int(seconds % 60) } 

@contextfunction
def block(context, block_name, *args, **kwargs):
    module_name = "block.%s" % (block_name,)
    __import__(module_name)
    block_function = sys.modules[module_name].block
    block_argspec = inspect.getargspec(block_function)

    block_call_args = {}
    for i in range(0, len(block_argspec.args)):
        arg = block_argspec.args[i]

        if i < len(args):            
            block_call_args[arg] = args[i]
        elif arg in kwargs:
            block_call_args[arg] = kwargs[arg]
        elif arg in context:
            block_call_args[arg] = context[arg]
        elif i >= len(block_argspec.args) - len(block_argspec.defaults):
            pass
        else:
            raise "Invalid block call"

    if "request" not in block_call_args:
        @cache.cache("block_%s" % block_name)
        def cached_block_function(kwargs):
            return block_function(**kwargs)
        result = cached_block_function(block_call_args)
    else:
        # request-dependent block: not cacheable
        result = block_function(**block_call_args)
    
    if result is not None:
        return Markup(jinja.get_template("block/%s.html" % (block_name,)).render(**result))
    else:
        return ""
jinja.globals["block"] = block
