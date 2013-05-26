#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from lxml.etree import tostring
from lxml.html.soupparser import fromstring
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import re
from werkzeug.utils import escape

from config import config

def vidog(text):
    return text.replace("\r", "")

def source(text):
    text = re.sub("\s+<source", "<source", text)
    text = re.sub("</source>\s+", "</source>", text)
    text = text.replace("<source>\n", "<source>")
    text = text.replace("\n</source>", "</source>")
    for symbol in [("<", "&lt;"), (">", "&gt;")]:
        r = re.compile("<source(.*?)>(.*?)" + symbol[0] + "(.*?)</source>", flags=re.DOTALL)
        while re.search(r, text):
            text = re.sub(r, "<source\\1>\\2" + symbol[1] + "\\3</source>", text)
    text = re.sub(r"&lt;source(.*?)&gt;", "<source\\1>", text)
    text = text.replace("&lt;/source&gt;", "</source>")
    return text

def quote(text):
    text = re.sub("\s+<quote>", "<quote>", text)
    text = re.sub("</quote>\s+", "</quote>", text)
    text = text.replace("<quote>", "<blockquote>").replace("</quote>", "</blockquote>")
    return text

def newlines(text):
    text = text.replace("\n", "<br />\n")
    # Not inside <source>!
    r = re.compile("<source(.*?)<br />(.*?)</source>", flags=re.DOTALL)
    while re.search(r, text):
        text = re.sub(r, "<source\\1\\2</source>", text)
    r = re.compile("<source>(.*?)<br />(.*?)</source>", flags=re.DOTALL)
    while re.search(r, text):
        text = re.sub(r, "<source>\\1\\2</source>", text)
    return text

def html_tags(text):
    text = tostring(fromstring(text), pretty_print=True, encoding="utf-8")
    
    soup = BeautifulSoup(text)
    for tag in soup.find_all():
        if tag.name not in ["html", "body", "p", "br", "b", "i", "s", "u", "var", "a", "img", "source", "pre", "blockquote"]:
            tag.extract()
        if tag.name == "p":
            tag.unwrap()

        new_attrs = {}
        if tag.name == "a":
            try:
                if tag.attrs["href"].startswith("http://") or tag["href"].startswith("https://"):
                    new_attrs["href"] = tag["href"]
                else:
                    tag.extract()
            except:
                tag.extract()
        if tag.name == "img":
            try:
                if tag["src"].startswith("http://") or tag["src"].startswith("https://"):
                    new_attrs["src"] = tag["src"]
                else:
                    tag.extract()
            except:
                tag.extract()
        # <source>
        if tag.name == "source":
            try:
                tag.replace_with(BeautifulSoup(highlight(u''.join([unicode(i).replace("&lt;", "<").replace("&gt;", ">") for i in tag.contents]), get_lexer_by_name(tag["lang"], stripall=True, startinline=True), HtmlFormatter(cssclass="syntax"))))
            except:
                tag.replace_with(BeautifulSoup(u'<pre>' + u''.join([unicode(i).replace("&lt;", "<").replace("&gt;", ">") for i in tag.contents]) + u'</pre>'))
        tag.attrs = new_attrs
    text = str(soup).decode("utf-8")

    text = text.replace("<html>", "")
    text = text.replace("</html>", "")
    text_old = ""
    while len(text_old) != len(text):
        text_old = text
        text = text.strip()
        text = re.sub("^<br />", "", text)
        text = re.sub("<br />$", "", text)

    return text

def smilies(text):
    for smilie in config.smilies:
        text = text.replace(escape(smilie), '<img class="smilie" src="' + config.url + config.smilies[smilie] + '" />')
    return text

all = [
    vidog,
    source,
    quote,
    newlines,
    html_tags,
    smilies,
]
