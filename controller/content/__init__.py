#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import dateutil.parser
from math import ceil
import operator
import PyRSS2Gen
import re
import simplejson
import StringIO
from sqlalchemy import distinct, func
from sqlalchemy.orm import subqueryload
import time
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Response

from cache import cache
from config import config
from controller.abstract import Controller as Abstract
from controller.content.comment_text_processor import all as all_comment_text_processor
from controller.content.model import ContentItem, Tag, Comment
from db import db
from middleware.authorization import admin_action
from middleware.authorization.model import User
from social_service import all as all_social_service

class Controller(Abstract):
    def __init__(self, types, feeds):
        self.types = types

        self.feeds = feeds
        for feed in self.feeds:
            # Feed default settings
            self.feeds[feed] = dict({
                "rss_allow" : True,
                "rss_items" : 10,

                "tag_allow" : True,

                "per_page"  : 10,
            }, **self.feeds[feed])

        self.export_function(globals(), "get_content_feeds", lambda: self.feeds)
        self.export_function(globals(), "process_content_item", self._item_dict)
        self.export_function(globals(), "process_comment_text", self._process_comment_text)

    def get_routes(self):
        rules = []
        # view single content item
        for type in self.types:
            if "view_url" in self.types[type]:
                rules.append(Rule("/" + self.types[type]["view_url"] + "/", endpoint="view", defaults={"type" : type}))
        # feeds
        for feed in self.feeds:
            if self.feeds[feed]["url"] == "":
                prefix = ""
            else:
                prefix = "/" + self.feeds[feed]["url"]
            rules.append(Rule(prefix + "/", endpoint="feed", defaults={"feed" : feed}))
            rules.append(Rule(prefix + "/page/<int:page>/", endpoint="feed", defaults={"feed" : feed}))
            rules.append(Rule(prefix + "/json/", endpoint="feed", defaults={"feed" : feed, "format" : "json"}))
            if self.feeds[feed]["tag_allow"]:
                rules.append(Rule(prefix + "/tag/<tag>/", endpoint="feed", defaults={"feed" : feed}))
                rules.append(Rule(prefix + "/tag/<tag>/page/<int:page>/", endpoint="feed", defaults={"feed" : feed}))
                rules.append(Rule(prefix + "/tag/<tag>/json/", endpoint="feed", defaults={"feed" : feed, "format" : "json"}))
            if self.feeds[feed]["rss_allow"]:
                rules.append(Rule(prefix + "/rss/", endpoint="feed", defaults={"feed" : feed, "format" : "rss"}))
        # post comment
        rules.append(Rule("/content/post-comment/<int:id>/", endpoint="post_comment"))
        rules.append(Rule("/content/edit-comment/<int:id>/", endpoint="edit_comment"))
        # user comments
        rules.append(Rule("/user/<int:id>/comments-for/rss/", endpoint="comments_for_user_rss"))
        # admin
        rules.append(Rule("/admin/content/",                endpoint="admin"))
        rules.append(Rule("/admin/content/new/<type>/",     endpoint="admin_new"))
        rules.append(Rule("/admin/content/edit/<int:id>/",  endpoint="admin_edit"))
        return rules

    def execute_view(self, request, **kwargs):
        url = kwargs["url"]
        type = kwargs["type"]
        content_item = db.query(ContentItem).filter(ContentItem.type == type, ContentItem.type_key == url, ContentItem.permissions_for(request.user)).first()
        if content_item is None:
        	raise NotFound()
        item_dict = self._item_dict(content_item)
        return self.render_to_response(request, [
            "content/type/%s/view.html" % (item_dict["type"],),
            "content/type/%s/view.html" % (item_dict["base_type"],),
        ], **{
            "meta_properties"   :   {
                                        "og_description"    : item_dict["description"],
                                        "og_image"          : item_dict["image"],

                                    },
            "breadcrumbs"       :   [item_dict["title"]],
            "body_class"        :   "view " + item_dict["base_type"] + " " + item_dict["type"],
            "item"              :   item_dict,
        })

    def execute_feed(self, request, **kwargs):        
        feed = self.feeds[kwargs["feed"]]
        format = kwargs.get("format", "html")

        f = self.feeds[kwargs["feed"]]["url"]
        q = db.query(ContentItem).filter(ContentItem.type.in_(feed["types"]), ContentItem.permissions_for(request.user)).options(subqueryload("comments"), subqueryload("tags"))
        t = []

        if "tag" in kwargs:
            tag = db.query(Tag).filter(Tag.url == kwargs["tag"]).first()
            if tag is None:
                raise NotFound()
            f += "/tag/" + kwargs["tag"]
            q = q.filter(ContentItem.id.in_([content_item.id for content_item in tag.content_items]))
            t.append(tag.title)

        if feed["rss_allow"]:
            rss_url = config.url + "/" + feed["url"] + "/rss/" if feed["url"] != "" else config.url + "/rss/"
            rss_title = config.build_title(feed["title"])

            if format == "rss":
                items = q.order_by(-ContentItem.created_at)[:feed["rss_items"]]
                rss = PyRSS2Gen.RSS2(
                    title           =   rss_title,
                    link            =   rss_url,
                    description     =   "",
                    lastBuildDate   =   datetime.now(),

                    items           =   [
                                            PyRSS2Gen.RSSItem(
                                                title       = item_dict["title"],
                                                link        = item_dict["url"],
                                                description = item_dict["description"],
                                                guid        = PyRSS2Gen.Guid(item_dict["url"]),
                                                pubDate     = item.created_at
                                            )
                                            for item_dict in [self._item_dict(item) for item in items]
                                        ]
                )
                rss_string = StringIO.StringIO()
                rss.write_xml(rss_string, "utf-8")
                return Response(rss_string.getvalue(), mimetype="application/rss+xml")
        else:
            rss_url = None
            rss_title = None

        if format == "json":
            count = int(request.args.get("count", "100"))
            if "before" in request.args:
                q = q.filter(ContentItem.created_at < dateutil.parser.parse(request.args["before"])).order_by(-ContentItem.created_at)
            elif "after" in request.args:
                q = q.filter(ContentItem.created_at > dateutil.parser.parse(request.args["after"])).order_by(ContentItem.created_at)
            else:
                q = q.order_by(-ContentItem.created_at)
            items = q[:count]
        else:
            title = [feed["title"]] + t

            if "page" in kwargs:
                page = kwargs["page"]
                items = list(reversed(q.order_by(ContentItem.created_at)[(page - 1) * feed["per_page"] : page * feed["per_page"]]))
                if len(items) == 0:
                    raise NotFound()
                items_skipped = q.filter(ContentItem.created_at > items[0].created_at).count()
            else:
                page = None
                items = q.order_by(-ContentItem.created_at)[:feed["per_page"]]
                items_skipped = 0

            dates = [created_at for (created_at,) in q.order_by(ContentItem.created_at).values(ContentItem.created_at)]
            pages = list(reversed([
                (
                    page,
                    dates[page * feed["per_page"]],
                    dates[min((page + 1) * feed["per_page"], len(dates)) - 1]
                )
                for page in xrange(0, int(ceil(float(len(dates)) / feed["per_page"])))
            ]))

            seasons = []
            month2season = {
                1 : "winter",
                2 : "winter",
                3 : "spring",
                4 : "spring",
                5 : "spring",
                6 : "summer",
                7 : "summer",
                8 : "summer",
                9 : "autumn",
               10 : "autumn",
               11 : "autumn",
               12 : "winter"
            }
            for date in dates:
                if len(seasons) == 0 or seasons[-1][0] != month2season[date.month]:
                    seasons.append((month2season[date.month], 1))
                else:
                    seasons[-1] = (seasons[-1][0], seasons[-1][1] + 1)
            seasons = list(reversed(seasons))

        items_formatted = [
            "<div class=\"content_item " + item_dict["base_type"] + " " + item_dict["type"] + " " + " ".join(item_dict["permissions"]) + "\" data-created-at=\"" + item_dict["created_at"].isoformat() + "\">" +
            self.render_template(request, [
                "content/type/%(type)s/preview_in_%(feed)s.html"        % { "type" : item_dict["type"], "base_type" : item_dict["base_type"], "feed" : kwargs["feed"] },
                "content/type/%(type)s/preview.html"                    % { "type" : item_dict["type"], "base_type" : item_dict["base_type"], "feed" : kwargs["feed"] },
                "content/type/%(base_type)s/preview_in_%(feed)s.html"   % { "type" : item_dict["type"], "base_type" : item_dict["base_type"], "feed" : kwargs["feed"] },
                "content/type/%(base_type)s/preview.html"               % { "type" : item_dict["type"], "base_type" : item_dict["base_type"], "feed" : kwargs["feed"] },
            ], item=item_dict) +
            "</div>"
            for (item_dict,) in [(self._item_dict(item),) for item in items]
        ]
        if format == "json":
            return Response(simplejson.dumps(items_formatted), mimetype="application/json")
        else:
            return self.render_to_response(request, [
                "content/feed/%s/feed.html" % (kwargs["feed"],),
                "content/feed/feed.html",
            ], **{
                "breadcrumbs"       :   title,
                "rss_url"           :   rss_url,
                "rss_title"         :   rss_title,
                "body_class"        :   "feed " + kwargs["feed"],
                "feed"              :   kwargs["feed"],
                "feed_url"          :   f.lstrip("/"),
                "items"             :   "".join(items_formatted),
                "items_skipped"     :   items_skipped,
                "pagination"        :   {
                                            "page"      :   page,
                                            "pages"     :   pages,
                                            "seasons"   :   seasons,
                                            "url"       :   re.sub("/page/([0-9]+)/", "/", request.path),
                                            "per_page"  :   feed["per_page"],
                                        },
            })

    def execute_post_comment(self, request, **kwargs):
        content_item = db.query(ContentItem).get(kwargs["id"])
        if request.form["email"] == "" and request.form["text"].strip() != "":
            comment = Comment()
            if request.user:
                comment.identity_id = request.user.default_identity.id
            comment.text = request.form["text"]
            comment.analytics = {
                "ip" : request.remote_addr
            }
            content_item.comments.append(comment)
            db.flush()

        return redirect(self._item_dict(content_item)["url"] + "#last-comment")

    def execute_edit_comment(self, request, **kwargs):
        comment = db.query(Comment).get(kwargs["id"])
        if request.user and request.user.id == comment.identity.user.id:
            if db.query(Comment).filter(Comment.content_item_id == comment.content_item_id, Comment.created_at > comment.created_at).count() > 0:
                response = {"error" : u"К сожалению, пока вы редактировали комментарий, его успели увидеть другие пользователи. Обновите страницу, чтобы увидеть их реакцию на ваш позор."}
            else:
                if (request.form["text"].strip() == ""):
                    db.delete(comment)
                    response = {"deleted" : True}
                else:
                    comment.text = request.form["text"]
                    response = {"text" : self._process_comment_text(comment.text)}
                db.flush()

            return Response(simplejson.dumps(response), mimetype="application/json")

        raise Forbidden()

    def execute_comments_for_user_rss(self, request, **kwargs):
        user = db.query(User).get(kwargs["id"])
        content_item_ids_user_commented = db.query(distinct(Comment.content_item_id)).filter(Comment.identity_id.in_([identity.id for identity in user.identities]))
        
        rss = PyRSS2Gen.RSS2(
            title           =   config.build_title(u"Новые комментарии для %s" % (all_social_service[user.default_identity.service].get_user_name(user.default_identity.service_data))),
            link            =   config.url + request.path,
            description     =   "",
            lastBuildDate   =   datetime.now(),

            items           =   [
                                    PyRSS2Gen.RSSItem(
                                        title       = u"%(username)s - %(title)s" % {
                                            "username"  : all_social_service[comment.identity.user.default_identity.service].get_user_name(comment.identity.user.default_identity.service_data),
                                            "title"     : self._item_dict(comment.content_item)["title"],
                                        },
                                        link        = self._item_dict(comment.content_item)["url"] + "#comment-%d" % (
                                            db.query(func.count(Comment)).filter(Comment.content_item == comment.content_item, Comment.created_at < comment.created_at).scalar() + 1
                                        ),
                                        description = self._process_comment_text(comment.text),
                                        guid        = PyRSS2Gen.Guid(self._item_dict(comment.content_item)["url"] + "#comment-%d" % (
                                            db.query(func.count(Comment)).filter(Comment.content_item == comment.content_item, Comment.created_at < comment.created_at).scalar() + 1
                                        )),
                                        pubDate     = comment.created_at
                                    )
                                    for comment in db.query(Comment).filter(
                                        Comment.content_item_id.in_(content_item_ids_user_commented),
                                        ~Comment.identity_id.in_([identity.id for identity in user.identities])
                                    ).order_by(-Comment.created_at)[:50]
                                ]
        )
        rss_string = StringIO.StringIO()
        rss.write_xml(rss_string, "utf-8")
        return Response(rss_string.getvalue(), mimetype="application/rss+xml")

    @admin_action
    def execute_admin(self, request):
        filter_types = [("", u"все")] + sorted([(k, v["type"].item_cases[0]) for k, v in self.types.items()], key=operator.itemgetter(1))
        create_types = sorted([("/admin/content/new/%s/" % k, v["type"].item_cases[3]) for k, v in self.types.items() if v["type"].get_editor() is not None], key=operator.itemgetter(1))

        q = db.query(ContentItem).filter(ContentItem.type.in_(self.types.keys())).order_by(-ContentItem.created_at)
        if request.args.get("type", ""):
            filter_type = request.args["type"]
            q = q.filter(ContentItem.type == filter_type)
        else:
            filter_type = ""

        total_pages = int(ceil(q.count() / 100.0))
        page = request.args.get("page", 1, type=int)
        
        content_items = [(
            self.types[content_item.type]["type"].item_cases[0],
            "/admin/content/edit/%d/" % content_item.id if self.types[content_item.type]["type"].get_editor() else None,
            self._item_dict(content_item),
        ) for content_item in q[(page - 1) * 100 : page * 100]]

        return self.render_to_response(request, "content/admin.html", **{
            "breadcrumbs"       :   [u"Управление контентом"],

            "filter_types"      :   filter_types,
            "create_types"      :   create_types,

            "filter_type"       :   filter_type,

            "total_pages"       :   total_pages,
            "page"              :   page,

            "content_items"     :   content_items,
        })

    @admin_action
    def execute_admin_new(self, request, type):
        c = ContentItem()
        c.type = type
        c.type_key = str(int(time.time()))
        c.created_at = datetime.now()
        c.permissions = ContentItem.permissions_NOT_READY
        c.data = self.types[c.type]["type"].get_editor().new_db()
        db.add(c)
        db.flush()

        return redirect("/admin/content/edit/%d/" % c.id)

    @admin_action
    def execute_admin_edit(self, request, id):
        c = db.query(ContentItem).get(id)
        if c is None:
            raise NotFound()

        editor = self.types[c.type]["type"].get_editor()

        if request.method == "POST":
            c.type_key = request.form["type_key"]
            c.created_at = dateutil.parser.parse(request.form["created_at"])
            c.permissions = ContentItem.permissions_PUBLIC if "public" in request.form else ContentItem.permissions_NOT_READY

            c.tags = []
            for tag in request.form["tags"].split(","):
                tag = tag.strip()
                db_tag = db.query(Tag).filter(Tag.title == tag).first()
                if db_tag is None:
                    db_tag = Tag()
                    db_tag.url = tag.split(":", 2)[0] if ":" in tag else tag
                    db_tag.title = tag.split(":", 2)[1] if ":" in tag else tag
                    db.add(db_tag)
                    db.flush
                c.tags.append(db_tag)

            data = editor.form_to_db(request, c.data)
            c.data = None
            db.flush()
            c.data = data
            db.flush()

            cache.get_cache("content_item_%d" % c.id).remove_value(key="formatter_output")

            return redirect(request.path)
        else:
            form = editor.db_to_form(c.data)

            return self.render_to_response(request, [
                "content/type/%s/edit.html" % (c.type,),
                "content/type/%s/edit.html" % (self._base_type(c.type),),
            ], **{
                "breadcrumbs"       :   [u"Редактирование %s" % self.types[c.type]["type"].item_cases[1]],

                "form"              :   form,
                "content_item"      :   c,
                "tags"              :   u",".join([t.title for t in c.tags]),
            })

    def _base_type(self, type):
        return self.types[type]["type"].__class__.__module__.split(".")[-1]

    def _item_dict(self, content_item):
        base_type = self._base_type(content_item.type)
        url = config.url + "/" + self.types[content_item.type]["view_url"].replace("<url>", content_item.type_key) + "/" if "view_url" in self.types[content_item.type] else None

        formatter = self.types[content_item.type]["type"].get_formatter()
        format = lambda: dict({
            "title"         : formatter.get_title(content_item),
            "image"         : formatter.get_image(content_item),
            "description"   : formatter.get_description(content_item, url),
            "text"          : formatter.get_text(content_item, url),
        }, **formatter.get_dict(content_item, url))
        if formatter.is_context_dependent(content_item):
            formatter_output = format()
        else:
            formatter_output = cache.get_cache("content_item_%d" % content_item.id).get(key="formatter_output", createfunc=format)

        return dict({
            "id"            : content_item.id,
            "type"          : content_item.type,
            "type_key"      : content_item.type_key,
            "created_at"    : content_item.created_at,            
            "comments"      : content_item.comments,
            "tags"          : content_item.tags,
            "permissions"   : [k for k in ContentItem.__dict__.keys() if k.startswith("permissions_") and isinstance(getattr(ContentItem, k), int) and content_item.permissions & getattr(ContentItem, k)],

            "base_type"     : base_type,
            "url"           : url,
        }, **formatter_output)

    def _process_comment_text(self, comment_text):        
        try:
            for comment_text_processor in all_comment_text_processor:
                comment_text = comment_text_processor(comment_text)
            return comment_text
        except:
            from werkzeug.utils import escape
            return escape(comment_text)
