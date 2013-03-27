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

class MacAddress(TextField):
    @classmethod
    def is_available(cls, user):
        return True

    @classmethod
    def get_title(cls):
        return u"MAC-адрес"

    @classmethod
    def get_help(cls):
        return u"При подключении устройства с этим MAC-адресом к Wi-Fi точке, умный дом поймёт, что вы пришли в гости"

    @classmethod
    def get_extra(cls):
        return """
            <script type="text/javascript">
                $(function(){
                    var $input = $(".user-settings #MacAddress input");
                    $input.on("keyup", function(){
                        var mac = $input.val().toLowerCase().replace(/-/g, ":").replace(/[^0-9a-f:]/g, "");
                        if (mac != $input.val())
                        {
                            $input.val(mac);
                        }

                        $input.removeClass("error");
                        if (!$input.val().match(/^[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}$/))
                        {
                            $input.addClass("error");
                        }
                    });
                });
            </script>
        """

class DoCheckin(Checkbox):
    @classmethod
    def is_available(cls, user):
        for identity in user.identities:
            if identity.service == "foursquare":
                return True
        return False

    @classmethod
    def get_title(cls):
        return u"Чекиниться"

    @classmethod
    def get_help(cls):
        return u"Чекиниться каждый раз, когда вы приходите в гости в умный дом"

class RunScrobbler(Checkbox):
    @classmethod
    def is_available(cls, user):
        for identity in user.identities:
            if identity.service == "last.fm":
                return True
        return False

    @classmethod
    def get_title(cls):
        return u"Запускать скробблер"

    @classmethod
    def get_help(cls):
        return u"Скробблить в ваш last.fm-аккаунт, когда вы приходите в гости в умный дом"

all = [
    MacAddress,
    DoCheckin,
    RunScrobbler,
] 
