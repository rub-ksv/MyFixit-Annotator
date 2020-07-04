#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Handeling the images in Myfixit
# The new classes in pyfixit package are built upon the basic classes in pyfixit project
# https://github.com/xiongchiamiov/pyfixit

import urllib

from PIL import Image as Pil

from src.pyfixit.base import Base


class Image(Base):
    """An image that has been uploaded to the site.
    :var string standard: *(Lazy, Optional)* URL to the standard size of the
    """


    def __init__(self, image):
        # self.id = image['id']
        self.standard = image
        # self.medium = image['medium']
        # self.original = image['original']
        try:
            # noinspection PyUnresolvedReferences
            self.imagest = Pil.open(urllib.request.urlopen(self.standard))
        except Exception as e:
            self.imagest = None
            print('Image loading error', e)

    def __repr__(self):
        return '<Image %s>' % self.id

    def __eq__(self, other):
        if not isinstance(other, Image):
            return False

        return self.id == other.id

