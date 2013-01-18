#!/usr/bin/python
# -*- coding: utf-8 -*-

from config import config

def image(text, url):
    def image_cb(match):
        from lxml import etree
        image = etree.fromstring(match.group(0))

        import re
        src = image.get("src")
        original = re.sub("images/(.*?)([0-9]+)\.", "images/\\2.", src)

        from PIL import Image
        import StringIO, urllib2
        width, height = Image.open(StringIO.StringIO(urllib2.urlopen(config.url + src).read())).size

        if "class" in image.attrib:
            image.attrib["class"] = "image " + image.attrib["class"]
        div_attrs = ' '.join([k + '="' + image.get(k) + '"' if k in image.attrib else '' for k in ["class", "style"]])
        img_attrs = ' '.join([k + '="' + image.get(k) + '"' if k in image.attrib else '' for k in ["alt"]])

        html = '<img src="' + image.get("src") + '" ' + img_attrs + ' />'
        if src != original and ("class" in image.attrib and "noclick" not in image.attrib["class"]):
            html = '<a href="' + original + '" style="width: ' + str(width) + 'px;">' + html + '</a>'
        return '<div ' + div_attrs + '>' + html + '</div>'

    import re
    return re.sub(re.compile("<image.*?/>", flags=re.DOTALL), image_cb, text)

def audio(text, url):
    def audio_cb(match):
        return '<a class="flowplayer audio flowplayer-audio" href="' + match.group(1) + '">' + match.group(1) + '</a>'

    import re
    return re.sub(re.compile("<audio>(.*?)</audio>", flags=re.DOTALL), audio_cb, text)

def video(text, url):
    def video_cb(match):
        return '<a class="flowplayer video flowplayer-video" href="' + match.group(1) + '">' + match.group(1) + '</a>'

    import re
    return re.sub(re.compile("<video>(.*?)</video>", flags=re.DOTALL), video_cb, text)

def math(text, url):
    import os, re
    from subprocess import Popen, PIPE
    def math_cb(match):
        import hashlib
        hash = hashlib.md5(match.group(2))
        filename = os.path.join(config.path, "data/blog/math", hash.hexdigest() + ".png")
        if not os.path.exists(filename):
            Popen([
                "mv",
                os.path.join(
                    "/tmp",
                    Popen([
                        os.path.join(
                            config.path,
                            "w/extensions/Math/math/texvc"
                        ),
                        "/tmp",
                        "/tmp",
                        match.group(2),
                        "UTF-8"
                    ], stdout=PIPE).communicate()[0][1:33] + ".png"
                ),
                filename
            ]).communicate()
        return "<img class=\"math\" src=\"/data/blog/math/" + hash.hexdigest() + ".png\" " + match.group(1) + " />"
    return re.sub(re.compile("<math(.*?)>(.*?)</math>", flags=re.DOTALL), math_cb, text)

def smilie(text, url): 
    for smilie in config.smilies:
        text = text.replace("<smile>" + smilie + "</smile>", '<img class="smilie" src="' + config.url + config.smilies[smilie] + '" />')
        text = text.replace("<smilie>" + smilie + "</smilie>", '<img class="smilie" src="' + config.url + config.smilies[smilie] + '" />')
    return text

def source(text, url):
    import re
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
    return re.sub(
        re.compile("<source lang=\"(.*?)\">(.*?)</source>", flags=re.DOTALL),
        lambda match: highlight(
            match.group(2),
            get_lexer_by_name(match.group(1), stripall=True, startinline=True),
            HtmlFormatter(cssclass="syntax")
        ),
        text
    )

def footnote(text, url):
    import hashlib
    post_id = hashlib.sha256(url.encode("utf-8")).hexdigest()

    import re
    footnotes = []
    def footnote_cb(match):
        footnotes.append(match.group(1))
        return "<a class=\"footnote-sup\" name=\"footnote-sup-{0}-{1}\" href=\"#footnote-{0}-{1}\">{1}</a>".format(post_id, len(footnotes))
    text = re.sub(re.compile("<footnote>(.*?)</footnote>", flags=re.DOTALL), footnote_cb, text)
    if len(footnotes) > 0:
        text += "<div class=\"footnotes\">" + "".join([
                    u"<div class=\"footnote-{0}-{1}\">[<a name=\"footnote-{0}-{1}\" href=\"#footnote-sup-{0}-{1}\">{1}</a>] — {2}</div>".format(post_id, i + 1, footnotes[i])
                    for i in range(len(footnotes))
                ]) + "</div>"
    return text

# Кавычки-лапки
def bdquo_ldquo(text, url):
    text = text.replace(u"„", u"<span style=\"font-family: Arial, Helvetica, sans-serif;\">„</span>")
    text = text.replace(u"“", u"<span style=\"font-family: Arial, Helvetica, sans-serif;\">“</span>")
    return text

all = [
    image,
    audio,
    video,

    math,
    smilie,
    source,

    footnote,

    bdquo_ldquo,
] 
