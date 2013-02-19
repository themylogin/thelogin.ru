#!/usr/bin/python
# -*- coding: utf-8 -*-

def block(request, limit=None):
    from cache import cache

    try:
        links = cache.get_cache("sape", expire=3600).get(key="links", createfunc=load_links)
    except:
        links = cache.get_cache("sape", expire=300).get(key="links", createfunc=lambda: {})

    if request.path in links:
        if not hasattr(request, "sape_links_shown"):
            request.sape_links_shown = 0

        slc = links[request.path][request.sape_links_shown : request.sape_links_shown + limit if limit is not None else None]
        request.sape_links_shown += len(slc)

        if slc:
            return {
                "class" : "sape",
                "links" : links["__sape_delimiter__"].join(slc),
            }

    return None

def load_links():
    from config import config
    import urllib2, phpserialize
    return dict(
        map(
            lambda path_links: (path_links[0], [link.decode("windows-1251") for link in path_links[1].values()] if isinstance(path_links[1], dict) else path_links[1]),
            phpserialize.loads(
                urllib2.urlopen(urllib2.Request(
                    "http://dispenser-01.sape.ru/code.php?user={0}&host={1}".format(config.sape_user_id, config.sape_host)
                )).read()
            ).items()
        )
    )
