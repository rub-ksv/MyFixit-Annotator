#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The class DisObject represents a disassembled object
from src.pyfixit.base import Base


class DisObject(Base):
    def __init__(self, data):
        self.data = data
        if len(self.data) > 0:
            if isinstance(data['span'], str):
                self.span = [int(i) for i in data['span'].split('-')]
            else:
                self.span = [int(i) for i in data['span']]
            self.name = data['name'].strip().lower()
            if 'obj_index' in data.keys():
                self.obj_index = data['obj_index']
            else:
                self.obj_index = []
        else:
            self.name = self.span = self.obj_index = ''

    def __str__(self):
        return str(self.data)
