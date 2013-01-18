#!/usr/bin/python
# -*- coding: utf-8 -*-

class Engine:
    def get(self, directory, key):
        raise NotImplementedError

    def set(self, directory, key, value):
        raise NotImplementedError

    def delete(self, directory, key):
        raise NotImplementedError

    def all(self, directory):
        raise NotImplementedError
