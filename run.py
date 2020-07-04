#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MyFixit annotator
from src.web_app.app import runner

if __name__ == '__main__':
    import nltk

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')
    runner()
