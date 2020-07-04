#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Text of steps

# The new classes in pyfixit package are built upon the basic classes in pyfixit project
# https://github.com/xiongchiamiov/pyfixit


class WikiText(object):
    """A bit of marked-up text.

    :var string raw: The text including markup. Ex: ``'''bold'''``.
    :var string rendered: The rendered text. Ex: ``<strong>bold</strong>``.
    """

    def __init__(self, raw, rendered):
        self.raw = raw
        self.rendered = rendered
        # self.tokens = word_tokenize(raw)

    def __str__(self):
        return self.raw

    def __repr__(self):
        return '<WikiText: %s>' % self.raw
