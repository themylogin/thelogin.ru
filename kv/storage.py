#!/usr/bin/python
# -*- coding: utf-8 -*-

class Storage:
    def __init__(self, engine):
        self.engine = engine

    def __getitem__(self, key):
        return Directory(self.engine, key)

class Directory(dict):
    def __init__(self, engine, name):
        self.engine = engine
        self.name = name

    def __getitem__(self, key):
        return self.engine.get(self.name, key)

    def __setitem__(self, key, value):
        return self.engine.set(self.name, key, value)

    def __delitem__(self, key):
        return self.engine.delete(self.name, key)

    def __iter__(self):
        for (k, v) in self.engine.all(self.name):
            yield (k, v)
