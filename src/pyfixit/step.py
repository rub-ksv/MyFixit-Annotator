#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The class Step represents a step in manual
#


# The new classes in pyfixit package are built upon the basic classes in pyfixit project
# https://github.com/xiongchiamiov/pyfixit

from nltk.tokenize import sent_tokenize

from src.pyfixit.image import Image
from src.pyfixit.line import Line
from src.pyfixit.disobject import DisObject


class Step(object):
    """One step in a guide.

    :var int guideid: The id of the :class:`pyfixit.guide.Guide` owning this
                      step. Ex: ``5``.
    :var int stepid: This step's id. Ex: ``14``.
    :var int orderby: This step's location in its guide relative to the other
                      steps. Lower numbers come first. Counting starts at 0 and
                      should not duplicate or skip over any natural numbers. Ex:
                      ``0``.
    :var string title: The title of this step. May be an empty string.
    :var iterable lines: An iterable of the :class:`pyfixit.line.Line` objects
                         composing this step.
    :var iterable media: *(Optional)* A list of :class:`pyfixit.image.Image`
                         objects illustrating the step.
    """

    def __init__(self, guideid, stepid, attributes, data=None, noimage=True):
        self.guideid = guideid
        self.stepid = stepid
        self.video = None
        self.comments = []
        self.image = []

        self.lines = [Line(self.guideid, self.stepid, attributes, data=line)
                      for line in data['Lines']]

        self.text = [line.text for line in self.lines]
        self.text_clean = ' '.join(self.text)
        self.text_raw = data['Text_raw']
        self.sentences = sent_tokenize(self.text_clean)

        self.orderby = data['Order']
        if not noimage:
            for image in data['Images']:
                self.image.append(Image(image))

        if 'Tools' in data.keys():
            self.tools_annotation = data['Tools_annotated']
        else:
            self.tools_annotation = []

        if 'Step_level_parts' in data.keys():
            self.stepobject = data['Step_level_parts']
        else:
            self.stepobject = None

        if 'Word_level_parts_raw' in data.keys():
            self.wordobject = [DisObject(i) for i in data['Word_level_parts_raw']]
        else:
            self.wordobject = None

        if 'Removal_verbs' in data.keys():
            self.verbobject = [DisObject(i) for i in data['Removal_verbs']]
        else:
            self.verbobject = None

    def __str__(self):
        return self.text_raw
