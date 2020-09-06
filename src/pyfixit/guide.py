#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The class Guide represents a Manual
# The new classes in pyfixit package are built upon the basic classes in pyfixit project
# https://github.com/xiongchiamiov/pyfixit

from src.pyfixit.step import Step
from src.pyfixit.tool import Tool


class Guide(object):

    def __init__(self, json=None, db=None, gid=None, noimage = True):
        if json:
            attributes = json
            self.id = json['Guidid']
        else:
            self.id = gid
            attributes = db.find_one({"Guidid": gid})

        self.category = attributes['Category']
        self.ancestors = attributes['Ancestors']
        self.url = attributes['Url']
        self.title = attributes['Title']
        self._savetools(attributes['Toolbox'])
        self.steps = [Step(self.id, step['StepId'], attributes, data=step, noimage=noimage) for step in attributes['Steps']]


    def _savetools(self, tools):
        self.toolbox = []
        for tool in tools:
            self.toolbox.append(Tool(tool))
