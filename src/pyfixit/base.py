#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MyFixit annotator
# The new classes in pyfixit package are built upon the basic classes in pyfixit project
# https://github.com/xiongchiamiov/pyfixit


class Base(object):
    """Base object defining common behavior for all API objects.
    """

    def __getattr__(self, name):
        self.refresh()
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
