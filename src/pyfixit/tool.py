#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The class Tool represents a tool in a step

import re
import urllib

from PIL import Image

from src.pyfixit.base import Base


class Tool(Base):
    def __init__(self, tool):
        # self.type = tool['type']
        self.url = tool['Url']
        self.thumbnail = tool['Thumbnail']
        self.alphanumeric = re.compile('[^\w+.-]')
        self.name = self.clean_tool(tool['Name'])
        if self.thumbnail:
            # noinspection PyUnresolvedReferences
            self.image = Image.open(urllib.request.urlopen(self.thumbnail))
        else:
            self.image = None

    def __str__(self):
        return self.name

    def clean_tool(self, txt):
        txt = re.sub('(^\d x) ', '', txt)  # 1 X tool
        txt = self.alphanumeric.sub(' ', txt)  # non alpha numeric line #
        txt = re.sub(r'(\d+)(?=[^.\d+-])', r'\1 ', txt)  # 5mm->5 mm
        txt = re.sub('\s+', ' ', txt)  # multi spaces
        return txt.lower().strip()
