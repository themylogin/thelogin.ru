#!/usr/bin/python
# -*- coding: utf-8 -*-

def timeline_map(ll):
    return '<a href="http://maps.yandex.ru/?ll=%(ll)s&amp;pt=%(ll)s,pm2rdl&amp;l=map&amp;size=640,240&amp;z=14" style="display: block; background: url(/data/internet/http/static-maps.yandex.ru/1.x/%(ll)s_map_640x280_14.png?ll=%(ll)s&amp;pt=%(ll)s,pm2rdl&amp;l=map&amp;size=640,280&amp;z=14) center no-repeat; width: 100%%; height: 240px; margin: 4px 0;"></a>' % {
        "ll"    : ll,
    }
