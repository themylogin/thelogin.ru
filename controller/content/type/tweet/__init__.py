#!/usr/bin/python
# -*- coding: utf-8 -*-

import dateutil.parser
import re
import urllib2
import urlparse

from config import config
from controller.content.type import abstract
from kv import storage as kv_storage
from log import logger

class Type(abstract.Type):
    def __init__(
        self,

        service,
        
        item_cases      = (u"твит",     u"твита",   u"твиту",   u"твит",    u"твитом",  u"твите"),
        item_mcases     = (u"твиты",    u"твитов",  u"твитам",  u"твиты",   u"твитами", u"твитах"),
    ):
        abstract.Type.__init__(self, item_cases, item_mcases)

        self.service = service

    def get_provider(self):
        return Provider(self.service)

    def get_formatter(self):
        return Formatter()

    def get_editor(self):
        return None

class Provider(abstract.Provider):
    def __init__(self, service):
        self.service = service

    def provide(self):        
        for tweet in self.service.api.GetUserTimeline(include_entities=True, include_rts=True):
            tweet_as_dict = tweet.AsDict()

            urls = tweet.urls
            media = tweet.media
            if tweet.retweeted_status:
                urls += tweet.retweeted_status.urls
                media += tweet.retweeted_status.media

            def foursquare_ll(_4sq_url):
                redirect = urllib2.urlopen(urllib2.Request(_4sq_url))
                if "/checkin/" not in redirect.geturl():
                    return ""
                html = redirect.read()
                html = urllib2.urlopen(urllib2.Request("http://foursquare.com/v/" + re.search("\"?[vV]enue\"?:\s*{\"id\":\"([a-f0-9]+)\"", html).group(1))).read()
                return re.findall("\"lng\":([0-9.]+)", html)[-1] + "," + re.findall("\"lat\":([0-9.]+)", html)[-1]

            def foursquare_pic(_4sq_url):
                redirect = urllib2.urlopen(urllib2.Request(_4sq_url))
                if "/checkin/" not in redirect.geturl():
                    return ""
                html = redirect.read()
                if "og:image" not in html:
                    return ""
                url = re.search("content=\"([^\"]+)\" property=\"og:image\"", html).group(1)
                if "600x600" in url:
                    return url.replace("600x600", "original")
                else:
                    return ""

            def instagram_src(instagr_am_url):
                html = urllib2.urlopen(urllib2.Request(instagr_am_url)).read()
                return re.search("<img class=\"photo\" src=\"(.+?)\"", html).group(1)

            yield self.provider_item(
                id          =   tweet_as_dict["id"],
                created_at  =   dateutil.parser.parse(tweet_as_dict["created_at"]).replace(tzinfo=None) + config.timezone,
                data        =   tweet_as_dict,
                kv          =   {
                                    "t.co"          : [(url.url, url.expanded_url) for url in urls],
                                    "twimg"         : [(media["url"], media["media_url"]) for media in media],

                                    "twitpic"       : [(url.expanded_url, url.expanded_url.replace("http://twitpic.com", "http://twitpic.com/show/iphone"))
                                                       for url in urls if url.expanded_url.startswith("http://twitpic.com")],

                                    "4sq"           : [(url.expanded_url, lambda: foursquare_ll(url.expanded_url))
                                                       for url in urls if url.expanded_url.startswith("http://4sq.com")],
                                    "foursquare pic": [(url.expanded_url, lambda: foursquare_pic(url.expanded_url))
                                                       for url in urls if url.expanded_url.startswith("http://4sq.com")],

                                    "instagr.am"    : [(url.expanded_url, lambda: instagram_src(url.expanded_url))
                                                       for url in urls if url.expanded_url.startswith("http://instagr.am") or url.expanded_url.startswith("http://instagram.com")],
                                }
            )

class Formatter(abstract.Formatter):
    def __init__(self):
        pass

    def get_title(self, content_item):
        return """<a href="http://twitter.com/#!/%(screen_name)s">%(screen_name)s</a> <span class="light">%(name)s</span>""" % self.prefer_retweet(content_item.data)["user"]

    def get_image(self, content_item):
        return self.prefer_retweet(content_item.data)["user"]["profile_image_url"]

    def get_description(self, content_item, url):
        text = self.prefer_retweet(content_item.data)["text"]

        text = re.sub(r"(\A|\s)@(\w{2,})", r'\1<a href="http://twitter.com/#!/\2">@\2</a>', text)
        text = re.sub(r'(\A|\s)#(\w{2,})', r'\1<a href="http://search.twitter.com/search?q=%23\2">#\2</a>', text)

        for (url, _) in re.findall('(https?://t\.co/([0-9A-Za-z]+))', text):
            # t.co
            try:
                longurl = kv_storage["t.co"][url]
                parsed  = urlparse.urlparse(longurl)
                tinyurl = (parsed.netloc + parsed.path + parsed.query).rstrip("/")
                if len(tinyurl) > 30:
                    tinyurl = tinyurl[:29] + "..."
                
                text = text.replace(url, '<a href="%(longurl)s">%(tinyurl)s</a>' % {
                    "longurl"   : longurl,
                    "tinyurl"   : tinyurl
                })
                continue
            except KeyError:
                pass

            # twimg
            try:
                twimg = kv_storage["twimg"][url].replace(":large", "")
                
                text = text.replace(url, '<a href="%(url)s">%(url)s</a>' % {
                    "url"   : url
                })
                text += '<a class="block" href="/data/internet/%(twimg)s"><img class="block" src="/data/internet/480/%(twimg)s" /></a>' % {
                    "twimg" : twimg.replace("://", "/"),
                }
                continue
            except KeyError:
                pass

            logger.warning(u"neither kv_storage[\"t.co\"][\"%s\"] nor kv_storage[\"twimg\"][\"%s\"] found", url, url)

        # 4sq
        for (url, _) in re.findall('(http://4sq\.com/([0-9A-Za-z]+))', text):
            try:
                ll = kv_storage["4sq"][url]
                if ll:
                    from controller.content.utils import timeline_map
                    text += timeline_map(ll)
            except KeyError:
                logger.warning(u"kv_storage[\"4sq\"][\"%s\"] not found", url)

        # foursquare pic
        for (url, _) in re.findall('(http://4sq\.com/([0-9A-Za-z]+))', text):
            try:
                pic = kv_storage["foursquare pic"][url]

                if pic:
                    text += '<a class="block" href="/data/internet/%(pic)s"><img class="block" src="/data/internet/480/%(pic)s" /></a>' % {
                        "pic" : pic.replace("://", "/"),
                    }
            except KeyError:
                logger.warning(u"kv_storage[\"foursquare pic\"][\"%s\"] not found", url)

        # twitpic
        for (url, _) in re.findall('(http://twitpic\.com/([0-9A-Za-z\-_]+))', text):
            try:
                twitpic = kv_storage["twitpic"][url]

                text += '<a class="block" href="/data/internet/%(twitpic)s"><img class="block" src="/data/internet/480/%(twitpic)s" /></a>' % {
                    "twitpic" : twitpic.replace("://", "/"),
                }
            except KeyError:
                logger.warning(u"kv_storage[\"twitpic\"][\"%s\"] not found", url)

        # instagram
        for (url, _, __) in re.findall('(http://(instagr\.am|instagram\.com)/p/([0-9A-Za-z\-_]+)/)', text):
            try:
                instagram = kv_storage["instagr.am"][url]
                
                text += '<a class="block" href="/data/internet/%(instagram)s"><img class="block" src="/data/internet/480/%(instagram)s" /></a>' % {
                    "instagram" : instagram.replace("://", "/"),
                }
            except KeyError:
                logger.warning(u"kv_storage[\"instagr.am\"][\"%s\"] not found", url)
                
        # i.vas3k.ru
        for url in re.findall('(http://i\.vas3k\.ru/[0-9A-Za-z\-_]+\.[0-9A-Za-z\-_]+)', text):
            text += '<a class="block" href="/data/internet/%(vas3k)s"><img class="block" src="/data/internet/480/%(vas3k)s" /></a>' % {
                "vas3k" : url.replace("://", "/"),
            }

        # storage.thelogin.ru/screenshots
        for url in re.findall('(http://storage\.thelogin\.ru/screenshots/[0-9A-Za-z\-_.:]+)', text):
            text += '<a class="block" href="%(href)s"><img class="block" src="/data/internet/480/%(src)s" /></a>' % {
                "href"  : url,
                "src"   : url.replace("://", "/"),
            }

        return text

    def get_text(self, content_item, url):
        return ""

    def get_dict(self, content_item, url):
        return {
            "is_copy"   : "retweeted_status" in content_item.data,
            "tweet"     : content_item.data,
        }

    #
    def prefer_retweet(self, data):
        return data.get("retweeted_status", data)
