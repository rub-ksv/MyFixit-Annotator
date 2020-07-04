#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Loading the constant values of the app
import os

APPNAME = "MyFixit Annotator"

root_path = os.path.join(os.path.abspath(os.curdir), 'src/')

# Mongodb address and port
mongo_address = '127.0.0.2:27001'

# Static folder for the web app. The images of the steps/tools, will be saved in this path
STATIC_FOLDER = os.path.join(root_path, 'web_app/static/')

Mac_subcategories = ['MacBook Pro 15" Retina', 'MacBook Pro 15"', 'MacBook Pro ', 'Mac Laptop']

# punctuations
puncs = (".", ",", "!", ";", "?", "(", ")", "[", "]", ":")

# a csv file contains the names and some stats of the categories
cat_stats = os.path.join(root_path, 'web_app/resources/cats.csv')

# path to the bilstm-crf model
ner_models = os.path.join(root_path, 'part_extraction/models/')

# the set of detachable objects and detaching verbs are read from these files.
# The files will be updated during the annotation.
detaching_verbs_file = os.path.join(root_path, 'web_app/resources/removal_verbs.txt')
detachable_objs_file = os.path.join(root_path, 'web_app/resources/detachable_objs.txt')
with open(detaching_verbs_file) as f:
    detaching_verbs = set(f.readlines())
with open(detachable_objs_file) as f:
    detachable_objs = set(f.readlines())

# initial set of headless objects
headless_objs = ('phillips', 'torx', 'flatheaded', 'hex')

# Initial set of interesting verb particles
verb_particles = {'off', 'up', 'away', 'out'}

# number of words for searching the particles
search_length = 5

# Initial set of words to remove from the noun phrase
bad_nouns = {'the', 'following', 'its', 'their'}
