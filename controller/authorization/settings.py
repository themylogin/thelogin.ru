#!/usr/bin/python
# -*- coding: utf-8 -*-

class Setting:
    @classmethod
    def render(cls, user):
        return """
            <label id="%(id)s">
                <div class="title">%(title)s</div>
                <div class="input">%(input)s</div>
                <div class="help">%(help)s</div>
                %(extra)s
            </label>
        """ % {
            "id"    : cls.get_id(),
            "title" : cls.get_title(),
            "input" : cls.get_input(user),
            "help"  : cls.get_help(),
            "extra" : cls.get_extra(),
        }

    @classmethod
    def get_id(cls):
        return cls.__name__

    @classmethod
    def get_value(cls, user):
        if cls.get_id() in user.settings:
            return user.settings[cls.get_id()]
        else:
            return cls.get_default_value()

    # Implement this
    @classmethod
    def is_available(cls, user):
        raise NotImplementedError

    @classmethod
    def get_title(cls):
        raise NotImplementedError

    @classmethod
    def get_help(cls):
        raise NotImplementedError

    @classmethod
    def get_input(cls, user):
        raise NotImplementedError

    @classmethod
    def get_extra(cls):
        return ""

    @classmethod
    def get_default_value(cls):
        raise NotImplementedError

    @classmethod
    def accept_value(cls, form):
        raise NotImplementedError

class Checkbox(Setting):
    @classmethod
    def get_input(cls, user):
        return """
            <input type="checkbox" name="%(id)s" value="1" %(chk)s />
            <div>%(help)s</div>
        """ % {
            "id"    : cls.get_id(),
            "chk"   : """checked="checked" """ if cls.get_value(user) else "",
            "help"  : cls.get_help(),
        }

    @classmethod
    def get_default_value(cls):
        return False

    @classmethod
    def accept_value(cls, form):
        return cls.get_id() in form

class TextField(Setting):
    @classmethod
    def get_input(cls, user):
        return """
            <input type="text" name="%(id)s" value="%(value)s" />
        """ % {
            "id"    : cls.get_id(),
            "value" : cls.get_value(user),
        }

    @classmethod
    def get_default_value(cls):
        return u""

    @classmethod
    def accept_value(cls, form):
        return form.get(cls.get_id())

###

all = [] 
