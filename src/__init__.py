#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MyFixit annotator
#



""" @mainpage docstring
MyFixit Annotator is a web app for the annotation of steps in MyFixit repair manuals with the required tool, disassembled
objects, and action verbs of diassembling.
The annotation guideline and the details of the dataset are interduced in this paper (link to the paper):

The app is optimized to speed up the annotation by following means:


Using an unsupervised method for the extraction of required tools and suggesting them, based on the Jaccard distance
between the bags of n-grams in text.

For the extraction of objects, either of the following two methods can be selected based on the amount of labeled data:


1- A state-of-the-art supervised approach based on a BiLSTM-CRF based sequence labeling architecture trained with mean
pooled contextualized embeddings .

2- A basic unsupervised approach which works based on a shallow parsing of the sentences and extracting the noun and
verb phrases. The parser is powered by a hierarchical BiLSTM-CRF architecture
trained on Conll-2000 corpus, (reference paper). The noun phrases will be further filtered using Wordnet, and a noun
is suggested only if any of its noun synsets have 'artifact' in its hypernyms.
It also keeps the track of the annotated objects and verbs during the annotation, and suggests those object/verbs in
future steps. In addition, it splits the sentences of the annotated steps and
uses the annotation of sentences for the next steps during the annotation.

How to Run:
    python3 run.py
"""
