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
        if user.settings and cls.get_id() in user.settings:
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
    def get_extra(cls, user):
        return ""

    @classmethod
    def get_default_value(cls):
        raise NotImplementedError

    @classmethod
    def accept_value(cls, form):
        raise NotImplementedError

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
        # мой мак-адрес 90-84-0D-9F-AD-3B!!!

all = [
    MacAddress,
] 
