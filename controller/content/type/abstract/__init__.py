#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import namedtuple

class Type(object):
    def __init__(
        self,

        item_cases      = (u"элемент",  u"элемента",    u"элементу",    u"элемент",     u"элементом",   u"элементе"),
        item_mcases     = (u"элементы", u"элементов",   u"элементам",   u"элементы",    u"элементами",  u"элементах")
    ):
        self.item_cases     = item_cases
        self.item_mcases    = item_mcases

    def get_provider(self):
        return Provider()

    def get_formatter(self):
        return Formatter()

    def get_editor(self):
        return Editor()

class Provider(object):
    _provider_item = namedtuple("provider_item", ["id", "started_at", "created_at", "data", "kv"])
    def provider_item(self, **kwargs):
        return self._provider_item(kwargs["id"], kwargs.get("started_at", None), kwargs["created_at"], kwargs["data"], kwargs.get("kv", {}))

    def lazy_provider_item(self, id, function):
        function_result = [None]
        class LazyProviderItem(object):
            def __getattr__(self, attr):
                if attr == "id":
                    return id
                else:
                    if function_result[0] is None:
                        function_result[0] = function()
                    return function_result[0][attr]
        return LazyProviderItem()

    def available(self):
        return True

    def provide(self):
        raise NotImplementedError

    def is_not_actual_item(self, content_item):
        # Will be called if item is not present in feed
        return True

    def on_item_inserted(self, content_item):
        pass

class Formatter(object):
    def is_context_dependent(self, content_item):
        return False

    def get_title(self, content_item):
        raise NotImplementedError

    def get_image(self, content_item):
        raise NotImplementedError

    def get_description(self, content_item, url):
        raise NotImplementedError

    def get_text(self, content_item, url):
        raise NotImplementedError

    def get_dict(self, content_item, url):
        raise NotImplementedError

class Editor(object):
    def new_db(self):
        raise NotImplementedError

    def db_to_form(self, db_data):
        raise NotImplementedError

    def form_to_db(self, request, db_data):
        raise NotImplementedError
