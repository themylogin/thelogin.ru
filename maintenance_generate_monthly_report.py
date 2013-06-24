#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import dateutil.relativedelta
import dateutil.parser
import itertools
import logging
import operator
import paramiko
from PIL import Image
import pymorphy2
import pytils
import re
import subprocess
import sys
import time
import urllib2

from config import config
from controller.content.model import ContentItem
from db import db
from log import logger
from middleware.authorization.model import User
from social_service import all as all_social_services
from utils import ucfirst

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../smarthome"))
from architecture.log import Record as SmarthomeEvent, db as smarthome_db
sys.path.pop()

desktop_ssh = paramiko.SSHClient()
desktop_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
desktop_ssh.connect("192.168.0.3", username="themylogin")

logger.handlers = []
logger.addHandler(logging.StreamHandler(sys.stderr))

start = dateutil.parser.parse(sys.argv[1] + "-01")
end = start + dateutil.relativedelta.relativedelta(months=1) - timedelta(seconds=1)

def get_outs(start, end):
    outs = []
    owner_is_at_home = None
    last_leave_datetime = None
    for event in smarthome_db.query(SmarthomeEvent).filter(
        SmarthomeEvent.smart == "owner_presence_watcher", SmarthomeEvent.attribute.in_(["came", "left"]),
        SmarthomeEvent.datetime >= start, SmarthomeEvent.datetime <= end,
    ).order_by(SmarthomeEvent.datetime):
        if owner_is_at_home is None:
            # Первое событие за интервал: узнаём, в начале интервала пользователь был дома или нет?
            if event.attribute == "came":
                # Пришёл, значит, не был
                owner_is_at_home = False
                last_leave_datetime = start
            else:
                # Ушёл, значит, был
                owner_is_at_home = True

        if owner_is_at_home and event.attribute == "left":
            owner_is_at_home = False
            last_leave_datetime = event.datetime
        elif not owner_is_at_home and event.attribute == "came":
            outs.append((last_leave_datetime, event.datetime))
            owner_is_at_home = True
        else:
            logger.warning(u"owner_is_at_home = %d и в %s произошло событие %s" % (owner_is_at_home, event.datetime.strftime("%Y-%m-%d %H:%M:%S"), event.attribute))
    # Если в конце интервала пользователь не дома, зафиксируем последний уход
    if not owner_is_at_home:
        outs.append((last_leave_datetime, end))

    return outs

def get_bike_rides(start, end):
    return [
        content_item
        for content_item in db.query(ContentItem).filter(ContentItem.type == "fitness_activity", ContentItem.created_at >= start, ContentItem.created_at <= end)
        if content_item.data["type"] == "Cycling"
    ]

def get_swimming_pool_checkins(start, end):
    return [
        tweet.created_at
        for tweet in db.query(ContentItem).filter(ContentItem.type == "tweet", ContentItem.created_at >= start, ContentItem.created_at <= end)
        if u"I'm at Бассейн Нептун" in tweet.data["text"] or u"@ Бассейн Нептун" in tweet.data["text"]
    ]

report_items = []
def report_item(callable):
    report_items.append(callable)

@report_item
def time_at_home():
    min_out_threshold = timedelta(minutes=5)

    outs = get_outs(start, end)

    time_out = sum([came - left for left, came in outs], timedelta())
    time_in = (end - start) - time_out

    looser_days = 0
    total_days = 0
    day = start
    while day < end:
        found_out = False
        for left, came in outs:
            if came - left > min_out_threshold and day.date() in [left.date(), came.date()]:
                found_out = True
                break
        if not found_out:
            entire_day_out = False
            for left, came in outs:
                if left < day and day < came:
                    entire_day_out = True
                    break
            if not entire_day_out:
                looser_days += 1

        day += timedelta(days=1)
        total_days += 1

    out_times = sum([1 if came - left > min_out_threshold else 0 for left, came in outs])

    return u"%(percent_time_at_home)d%% времени дома. Выходил на улицу %(out_times)s. %(looser_days)s из %(total_days)s имел «счастье» никуда не ходить вообще." % {
        "percent_time_at_home"  : time_in.total_seconds() / (end - start).total_seconds() * 100,
        "out_times"             : pytils.numeral.get_plural(out_times, (u"раз", u"раза", u"раз")),
        "looser_days"           : ucfirst(pytils.numeral.sum_string(looser_days, 1, (u"день", u"дня", u"дней"))),
        "total_days"            : u" ".join([pymorphy2.MorphAnalyzer().parse(word)[0].inflect({"gent"}).word for word in pytils.numeral.in_words(total_days).split()]),
    }

@report_item
def desktop_time():
    stdin, stdout, stderr = desktop_ssh.exec_command("cat /home/themylogin/Dev/theDesktopUtils/LifeMetrics/MouseOdometer.log")
    mouse_events = [(timestamp, pixels) for timestamp, pixels in [map(int, re.sub("[^0-9 ]", "", s).split(" ")) for s in filter(lambda s: s, stdout.read().split("\n"))]
                                        if timestamp >= time.mktime(start.timetuple()) and timestamp <= time.mktime(end.timetuple())]

    return u"%d%% времени за компьютером. Мышь прошла %.1f км." % (
        (len([pixels for timestamp, pixels in mouse_events if pixels > 0]) * 300) / (end - start).total_seconds() * 100,
        sum([pixels for timestamp, pixels in mouse_events]) / (1920 / 5.0 * 1e2) / 1e3,
    )

@report_item
def github():
    def get_github_additions_deletions(url):
        html = urllib2.urlopen(url).read()
        m1 = re.search(re.compile("<strong>([0-9,]+) addition", re.DOTALL), html)
        m2 = re.search(re.compile("<strong>([0-9,]+) deletion", re.DOTALL), html)
        return (int(m1.group(1).replace(",", "")), int(m2.group(1).replace(",", "")))

    url_base = ""
    projects = {}
    for content_item in db.query(ContentItem).filter(
        ContentItem.type == "github_action",
        ContentItem.created_at >= start, ContentItem.created_at <= end,
    ).order_by(ContentItem.created_at):
        m = re.search(re.compile("/([^/]+)/compare/([0-9a-f]+)\.\.\.([0-9a-f]+)", re.DOTALL), content_item.data["link"])
        if m:
            url_base = content_item.data["link"].replace(m.group(0), "")

            project = m.group(1)
            first_commit = m.group(2)
            last_commit = m.group(3)

            if project not in projects:
                projects[project] = {
                    "first_commit"  : first_commit,
                    "additions"     : 0,
                    "deletions"     : 0,
                }

            additions, deletions = get_github_additions_deletions(content_item.data["link"])
            projects[project]["additions"] += additions
            projects[project]["deletions"] += deletions
            projects[project]["last_commit"] = last_commit

    for project in projects:
        projects[project]["total_diff_url"] = url_base + "/%s/compare/%s...%s" % (
            project,
            projects[project]["first_commit"],
            projects[project]["last_commit"]
        )
        projects[project]["useful_additions"], projects[project]["useful_deletions"] = get_github_additions_deletions(projects[project]["total_diff_url"])

    if projects:        
        text = u"Написал %s кода для своих проектов (хотя можно было всего %d). Топ проектов:\n" % (
            pytils.numeral.get_plural(sum([projects[project]["additions"] for project in projects]), (u"строку", u"строки", u"строк")),
            sum([projects[project]["useful_additions"] for project in projects])
        )

        text += u"<ul>\n"
        for project, data in sorted(projects.items(), key=lambda kv: -kv[1]["additions"])[:5]:
            text += u"<li>%s: <a href=\"%s\">%d (%d) additions, %d (%d) deletions</a></li>\n" % (
                project,
                data["total_diff_url"],
                data["additions"],
                data["useful_additions"],
                data["deletions"],
                data["useful_deletions"],
            )
        text += u"</ul>\n"

        return text
    else:
        return None

@report_item
def git():
    git_repo = "/home/themylogin/www/ll.openstart.ru"
    
    last_commit = None
    first_commit = None
    for commit, date in re.findall(
        re.compile("commit ([0-9a-f]+).+?Date:(.+?)\n", re.DOTALL),
        subprocess.Popen(["sh", "-c", "cd %s && git log" % git_repo], stdout=subprocess.PIPE).communicate()[0]
    ):
        date = dateutil.parser.parse(date).replace(tzinfo=None)

        if date >= start and date <= end:
            first_commit = commit
            if last_commit is None:
                last_commit = commit

    additions = sum([int(l) for l in filter(lambda s: s, subprocess.Popen(["sh", "-c", "cd %s && git log %s..%s --oneline --shortstat | grep insertions | awk '{print $4}'" % (git_repo, first_commit, last_commit)], stdout=subprocess.PIPE).communicate()[0].split("\n"))])
    deletions = sum([int(l) for l in filter(lambda s: s, subprocess.Popen(["sh", "-c", "cd %s && git log %s..%s --oneline --shortstat | grep insertions | awk '{print $6}'" % (git_repo, first_commit, last_commit)], stdout=subprocess.PIPE).communicate()[0].split("\n"))])

    stat = subprocess.Popen(["sh", "-c", "cd %s && git diff --stat %s %s" % (git_repo, first_commit, last_commit)], stdout=subprocess.PIPE).communicate()[0]
    useful_additions = int(re.search(re.compile("([0-9]+) insertion", re.DOTALL), stat).group(1))
    useful_deletions = int(re.search(re.compile("([0-9]+) deletion", re.DOTALL), stat).group(1))

    return u"Написал %s кода для рабочего проекта (хотя можно было всего %d)." % (
        pytils.numeral.get_plural(additions, (u"строку", u"строки", u"строк")),
        useful_additions,
    )

@report_item
def music():
    outs = get_outs(start, end)
    bike_rides = get_bike_rides(start, end)
    swimming_pool_checkins = get_swimming_pool_checkins(start, end)

    Scrobble = all_social_services["last.fm"].thelogin_Scrobble
    scrobbles = all_social_services["last.fm"].thelogin_db.query(Scrobble).filter(
        Scrobble.user == all_social_services["last.fm"].thelogin_user.id,
        Scrobble.uts >= time.mktime(start.timetuple()), Scrobble.uts <= time.mktime(end.timetuple())
    ).order_by(Scrobble.uts)

    prev = 0
    total = 0
    total_at_home = 0
    for scrobble in scrobbles:
        if scrobble.uts - prev > 30 * 60:
            scrobble_length = 240
        else:
            scrobble_length = scrobble.uts - prev

        total += scrobble_length

        was_at_home = True
        for out in outs:
            if out[0] < datetime.fromtimestamp(scrobble.uts) and datetime.fromtimestamp(scrobble.uts) < out[1]:
                was_at_home = False
                break
        if was_at_home:
            total_at_home += scrobble_length

        prev = scrobble.uts

    def scrobbles_within_intervals(intervals):
        filtered_scrobbles = []
        for scrobble in scrobbles:
            for start, end in intervals:
                if start < datetime.fromtimestamp(scrobble.uts) and datetime.fromtimestamp(scrobble.uts) < end:
                    filtered_scrobbles.append(scrobble)
                    break
        return filtered_scrobbles

    swimming_pool_trips = []
    for checkin in swimming_pool_checkins:
        out_found = False
        for out in outs:
            if out[0] < checkin and checkin < out[1]:
                out_found = True
                if out[1] - out[0] < timedelta(hours=3):
                    swimming_pool_trips.append(out)
        if not out_found:
            logger.warning("Swimming pool checking %s created while owner was at home" % checkin.strftime("%Y-%m-%d %H:%M:%S"))

    charts = [
        (u"Все", scrobbles),
        (u"На велосипеде", scrobbles_within_intervals([(ride.started_at, ride.created_at) for ride in bike_rides])),
        (u"По дороге в бассейн «Нептун»", scrobbles_within_intervals(swimming_pool_trips)),
    ]

    chart_selectors = [
        (u"Лучшие исполнители", lambda scrobble: u"<a href=\"%s\">%s</a>" % (
            all_social_services["last.fm"].network.get_artist(scrobble.artist).get_url(),
            scrobble.artist
        )),

        #(u"Лучшие альбомы", lambda scrobble: u"<a href=\"%s\">%s – %s</a>" % (
        #    all_social_services["last.fm"].network.get_album(scrobble.artist, scrobble.album).get_url(),
        #    scrobble.artist,
        #    scrobble.album
        #) if scrobble.album else None),

        (u"Лучшие композиции", lambda scrobble: u"<a href=\"%s\">%s – %s</a>" % (
            all_social_services["last.fm"].network.get_track(scrobble.artist, scrobble.track).get_url(),
            scrobble.artist,
            scrobble.track
        )),
    ]

    charts_html = u""
    for title, selector in chart_selectors:
        titles = u""
        tables = u""
        first = True
        for chart_title, scrobbles in charts:
            titles += u"<li%s>%s</li>\n" % (" class=\"current\"" if first else "", chart_title)

            chart = sorted([(x, len(list(y))) for x, y in itertools.groupby(sorted(filter(lambda x: x is not None, map(selector, scrobbles))))], key=lambda t: -t[1])
            tables += u"<table%s>\n" % (" style=\"display: none;\"" if not first else "") + u"".join([
                u"\t<tr><td class=\"position\">%d</td><td class=\"subject\">%s</td><td class=\"bar\"><div style=\"width: %d%%;\"><div>%d</div></div></td></tr>\n" % (
                    i,
                    subject,
                    float(count) / chart[0][1] * 100,
                    count,
                )
                for i, subject, count in itertools.izip(range(1, 11), itertools.imap(operator.itemgetter(0), chart), itertools.imap(operator.itemgetter(1), chart))
            ]) + u"</table>"

            first = False

        charts_html += u"""<div class=\"lastfm-chart\">
            <div class="title">%s</div>

            <div class="tabs">
                <ul>
                    %s
                </ul>
                <div class="clear"></div>
            </div>

            <div class="charts">
                %s
            </div>
        </div>""" % (
            title,
            titles,
            tables,
        )

    return u"%d%% времени под музыку (%d%% дома).\n%s" % (
        total / (end - start).total_seconds() * 100,
        total_at_home / (end - start).total_seconds() * 100,
        charts_html,
    )

@report_item
def guests():
    guests = {}
    for event in db.query(ContentItem).filter(
        ContentItem.type.in_(["guest_in", "guest_out"]),
        ContentItem.created_at >= start, ContentItem.created_at <= end,
    ).order_by(ContentItem.created_at):
        identity = db.query(User).get(int(event.type_key.split(",")[0].split("=")[1])).default_identity
        username = all_social_services[identity.service].get_user_name(identity.service_data)

        if event.type == "guest_in":
            if guests.get(username, []) and guests[username][-1][1] is None:
                logger.warning("guest_in event %s should not be here" % event.type_key)
                continue

            if username not in guests:
                guests[username] = []
            guests[username].append((event.created_at, None))
        else:
            if guests.get(username, []) and guests[username][-1][1] is not None:
                logger.warning("guest_out event %s should not be here" % event.type_key)
                continue

            if username not in guests:
                guests[username] = [(start, None)]
            guests[username][-1] = (guests[username][-1][0], event.created_at)
    for username in guests:
        if guests[username][-1][1] is None:
            guests[username][-1] = (guests[username][-1][0], end)

    datetime_isStart = []
    for username in guests:
        for a, b in guests[username]:
            datetime_isStart.append((a, True))
            datetime_isStart.append((b, False))

    time_with_guests = timedelta()
    guests_in_house = 0
    last_party_start = None
    for datetime, is_start in sorted(datetime_isStart, key=lambda t: t[0]):
        if is_start:
            if guests_in_house == 0:
                last_party_start = datetime
            guests_in_house += 1
        else:
            guests_in_house -= 1
            if guests_in_house < 0:
                logger.warning("guests_in_house < 0")
                guests_in_house = 0
            time_with_guests += datetime - last_party_start

    if time_with_guests:        
        text = u"%d%% времени с гостями. Топ гостей:\n" % (time_with_guests.total_seconds() / (end - start).total_seconds() * 100)

        text += u"<ul>\n"
        for username, timedeltas in sorted(guests.items(), key=lambda kv: -sum([b - a for a, b in kv[1]], timedelta()))[:5]:
            text += u"<li>%s (%s)</li>\n" % (username, pytils.numeral.get_plural(int(sum([b - a for a, b in timedeltas], timedelta()).total_seconds() / 3600), (u"часов", u"часов", u"часов")))
        text += u"</ul>\n"

        return text
    else:
        return None

@report_item
def im():
    stdin, stdout, stderr = desktop_ssh.exec_command("/home/themylogin/Dev/theDesktopUtils/LifeMetrics/PidginHistoryTime.py %d %d" % (time.mktime(start.timetuple()), time.mktime(end.timetuple())))
    tim, bytes, messages = map(int, stdout.read().strip().split())

    return u"%d%% времени в IM. Принято и отправлено %s общим объёмом %s." % (
        tim / (end - start).total_seconds() * 100,
        pytils.numeral.get_plural(messages, (u"сообщение", u"сообщения", u"сообщений")),
        pytils.numeral.get_plural(int(bytes / 100) * 100, (u"символ", u"символа", u"символов")),
    )

@report_item
def tv():
    time = timedelta()
    for content_item in db.query(ContentItem).filter(ContentItem.type == "movie", ContentItem.created_at >= start, ContentItem.created_at <= end):
        this_time = content_item.created_at - content_item.started_at
        if this_time > timedelta(hours=3):
            this_time = timedelta(hours=3)

        time += this_time

    if time:
        return u"%d%% времени перед телевизором." % (time.total_seconds() / (end - start).total_seconds() * 100)
    else:
        return None

@report_item
def bike():
    bike_rides = get_bike_rides(start, end)

    times = len(bike_rides)
    m = sum([content_item.data["total_distance"] for content_item in bike_rides])
    seconds = sum([content_item.data["duration"] for content_item in bike_rides])

    if times > 0:
        return u"%s ездил на велосипеде (%.2f км., средняя скорость %.2f км/ч)" % (
            pytils.numeral.get_plural(times, (u"раз", u"раза", u"раз")),
            m / 1000.0,
            m * 3.6 / seconds
        )
    else:
        return None

@report_item
def swimming_pool():
    in_fact = len(get_swimming_pool_checkins(start, end))

    supposed = 0
    day = start
    while day < end:
        if day.isoweekday() in [1, 3, 5]:
            supposed += 1
        day += timedelta(days=1)

    return u"%s был в бассейне «Нептун» (а должен был %d)." % (
        pytils.numeral.get_plural(in_fact, (u"раз", u"раза", u"раз")),
        supposed,
    )

@report_item
def bank_card():
    shops = {}
    for content_item in db.query(ContentItem).filter(ContentItem.type == "vtb24_transaction", ContentItem.created_at >= start, ContentItem.created_at <= end):
        m = re.search(re.compile(u"произведена транзакция по (.+) на сумму ([0-9.]+) (.+?)\..+Детали платежа: (.+)\. Код авторизации", re.DOTALL), content_item.data["notification"])
        if m.group(1) == u"оплате":
            amount = float(m.group(2))
            if m.group(3) == "USD":
                amount *= 30
            elif m.group(3) == "RUR":
                pass
            else:
                logger.warning("Unknown currency: %s" % m.group(3))

            shop_name = m.group(4)

            if shop_name not in shops:
                shops[shop_name] = 0
            shops[shop_name] += amount

    if shops:
        text = u"Покупал товары. Топ магазинов:\n"

        text += u"<ul>\n"
        for shop_name, amount in sorted(shops.items(), key=lambda kv: -kv[1])[:5]:
            text += u"<li>%s (%s)</li>\n" % (shop_name, pytils.numeral.get_plural(int(amount), (u"рубль", u"рубля", u"рублей")))
        text += u"</ul>\n"

        return text
    else:
        return None

@report_item
def tcard():
    stat = {}
    for content_item in db.query(ContentItem).filter(ContentItem.type == "tcard_trip", ContentItem.created_at >= start, ContentItem.created_at <= end):
        if content_item.data["RouteType"] == u"метро":
            key = u"Метро «" + {
                "MARKS"             : u"Площадь Маркса",
                "STUD"              : u"Студенческая",
                "RECHV"             : u"Речной вокзал",
                "OKT"               : u"Октябрьская",
                "LENIN"             : u"Площадь Ленина",
                "KR-PR"             : u"Красный проспект",
                "GAGAR"             : u"Гагаринская",
                "ZAELC"             : u"Заельцовская",

                "G-M"               : u"Площадь Гарина-Михайловского",
                "POKR"              : u"Маршала Покрышкина",
                "BEREZ"             : u"Берёзовая роща",
                "NIVA"              : u"Золотая Нива",
            }[content_item.data["RouteNum"]] + u"»"
        else:
            key = ucfirst(content_item.data["RouteType"].split()[1]) + u" " + content_item.data["RouteNum"]

        if key not in stat:
            stat[key] = []
        stat[key].append(content_item.data["Summa"] / 100)

    if stat:
        text = u"Потратил на проезд %s (%s). Топ транспорта:\n" % (
            pytils.numeral.get_plural(sum([sum(l) for l in stat.values()]), (u"рубль", u"рубля", u"рублей")),
            pytils.numeral.get_plural(sum([len(l) for l in stat.values()]), (u"поездка", u"поездки", u"поездок")),
        )

        text += u"<ul>\n"
        for transport, amounts in sorted(stat.items(), key=lambda kv: -len(kv[1]))[:5]:
            text += u"<li>%s (%s)</li>\n" % (transport, pytils.numeral.get_plural(len(amounts), (u"поездка", u"поездки", u"поездок")))
        text += u"</ul>\n"

        return text
    else:
        return None

report = u"<p>Вот как прошёл у меня этот месяц:<cut></p>\n<ul>\n"
for f in report_items:
    item = f()
    if item:
        report += u"<li>" + item + u"</li>\n"
report += u"</ul>\n"

if sys.argv[2] == "post":
    title = ucfirst(pytils.dt.ru_strftime(u"%B %Y", date=start))

    now_playing = all_social_services["last.fm"].network.get_user(all_social_services["last.fm"].username).get_now_playing()
    if now_playing:
        music = u"%s – %s" % (now_playing.get_artist().get_name(), now_playing.get_title())
    else:
        music = ""

    post = ContentItem()
    post.type = "blog_post"
    post.type_key = pytils.translit.slugify(title)
    post.created_at = datetime.now()
    post.permissions = ContentItem.permissions_PUBLIC
    post.data = {
        "title"         : title,
        "title_html"    : "",
        "music"         : music,
        "text"          : report,

        "ipaddress"     : "127.0.0.1",
        "useragent"     : "Monthly report generator",
    }
    db.add(post)
    db.flush()
            
if sys.argv[2] == "print":
    print report
