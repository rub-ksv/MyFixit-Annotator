#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The class Line represents a line in a step
# The new classes in pyfixit package are built upon the basic classes in pyfixit project
# https://github.com/xiongchiamiov/pyfixit


import re


class Line(object):
    """One line of text in a step.

    :var int guideid: The id of the :class:`pyfixit.guide.Guide` owning this
                      step. Ex: ``5``.
    :var int stepid: The id of the :class:`pyfixit.step.Step` owning this step.
                     Ex: ``14``.
    :var string bullet: The color or type of the step's bullet. Ex: ``black``.
    :var int level: The number of levels in this step is indented. Ex: ``0``.
    :var string text: A :class:`pyfixit.wikitext.WikiText` of the step's text.
    """

    def __init__(self, guideid, stepid, attributes, data=None):
        self.guideid = guideid
        self.stepid = stepid
        if data:
            self._update(data)
        else:
            for step in attributes['Steps']:
                if step['StepId'] == self.stepid:
                    for line in step['Lines']:
                        # if line['Lineid'] == self.lineid:
                        self._update(line)
                        return
    def __str__(self):
        return self.text

    def _update(self, data):
        """Update the line using the blob of json-parsed data directly from the
        API.
        """
        # self.bullet = data['bullet']
        # self.level = data['level']
        # self.text_raw = data['text_raw']
        self.text = self.clean_step(data['Text'])

    @staticmethod
    def clean_step(txt):
        text = ''
        txt = re.sub(r'\[guide\|\d+\|.*\]', 'guide', txt)
        txt = re.sub(r'\[product\|.*\|(.*)\]', r'\1', txt)  # [product|IF179-010|thermal paste]
        for word in txt.split():
            if 'http' in word:
                word = re.sub("^.*http.*", '', word)  # remove the link
            word = re.sub(r'[^\'\w+.!,();/:?-]', '', word)  # non alpha numeric
            word = re.sub(r"(\d+)(?=[^.\d])", r'\1 ', word)  # 5mm
            word = re.sub(r'new_windowtrue', '', word)  # newwindow
            text += word.lower() + ' '
        # if not text.strip().endswith(('!', '.', '?', ";")) : #no end punctuation
        #     text += ' . '
        text = re.sub(r'([^0-9])([.,!?()\[\]:;])', r'\1 \2 ', text)  # this is necessary for syntactic parser
        text = re.sub('\s+', ' ', text)  # multi spaces

        return text
