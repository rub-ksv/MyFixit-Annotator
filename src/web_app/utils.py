#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Helper functions for the annotator app
import ast
import pickle as pk
import re
from builtins import any as b_any
from tqdm import tqdm

from PIL import Image
from flask import flash
from nltk.tokenize import sent_tokenize
from pymongo import MongoClient

from src.pyfixit import Guide
from src.web_app.constants import *


def start_db(address='127.0.0.2:27001'):
    """
    connecting database
    """
    connection = MongoClient(address)
    db = connection.myfixit
    posts = db.posts
    return posts


def docselect(posts, category):
    """
    Receives the category of devices and returns the relevant documents
    """
    search_filter = {'Ancestors': {"$in": [category]}, "$where": 'this.Toolbox.length>0'}
    postsample = posts.find(search_filter, no_cursor_timeout=True)
    print('{} document are selected'.format(postsample.count()), flush=True)
    return postsample


def save_obj(obj, name):
    """
    Saving the pickle object
    """
    with open(name + '.pkl', 'wb') as file:
        pk.dump(obj, file, pk.HIGHEST_PROTOCOL)


def load_obj(name):
    """
    loading the pickle object
    """
    with open(name + '.pkl', 'rb') as file:
        return pk.load(file)


def obj_checked(words, defaultset):
    """
    Selecting the prechecked checkboxes for the objects.
    :rtype: list
    """
    checked = []
    stringed = []
    for word in words:
        if word['name'].split()[-1] in defaultset:
            checked.append('checked')
        else:
            checked.append('')
        stringed.append("{} > {}-{}".format(word['name'], word['span'][0], word['span'][1]))
    return list(zip(stringed, checked))


def cleantxt(txt):
    """
    Removing non-alpha-numeric chars from string
    :rtype: str
    """
    return re.sub(r'[^\'\w+]', '', txt).lower().strip()


def tools_checked(tools, prediction):
    """
    Selecting the prechecked checkboxes for the tools.
    :rtype: list
    """
    checked = []
    for tool in tools:
        if tool['name'] in prediction:
            checked.append('checked')
        else:
            checked.append('')
    return list(zip(tools, checked))


def append_images(images, direction='vertical',
                  bg_color=(255, 255, 255), aligment='center'):
    """
    Appends images in horizontal/vertical direction.

    Args:
        images: List of PIL images
        direction: direction of concatenation, 'horizontal' or 'vertical'
        bg_color: Background color (default: white)
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center'

    Returns:
        Concatenated image as a new PIL image object.
    """
    widths, heights = zip(*(i.size for i in images if i))

    if direction == 'horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        assert isinstance(widths, object)
        new_width = max(widths)
        new_height = sum(heights)

    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)

    offset = 0
    for im in images:
        if im:
            if direction == 'horizontal':
                y = 0
                if aligment == 'center':
                    y = int((new_height - im.size[1]) / 2)
                elif aligment == 'bottom':
                    y = new_height - im.size[1]
                new_im.paste(im, (offset, y))
                offset += im.size[0]
            else:
                x = 0
                if aligment == 'center':
                    x = int((new_width - im.size[0]) / 2)
                elif aligment == 'right':
                    x = new_width - im.size[0]
                new_im.paste(im, (x, offset))
                offset += im.size[1]

    return new_im


def check_statics():
    """
    Checking the folder of steps and tools' images and create the directories if not exist
    :rtype: str, str
    """
    imagepath = os.path.join(STATIC_FOLDER, 'images')
    steppath = os.path.join(imagepath, "steps")
    if not os.path.exists(steppath):
        os.makedirs(steppath)
    toolpath = os.path.join(imagepath, "tools")
    if not os.path.exists(toolpath):
        os.makedirs(toolpath)
    return toolpath, steppath


def download_images(posts, category):
    """
    Downloading the images of the steps and tools
    """
    annotated_steps = find_annotateds(posts, category)
    toolpath, steppath = check_statics()
    cursor = docselect(posts, category)
    for counter, d in enumerate(cursor):
        doc = Guide(d)
        toolbox = []
        for t in doc.toolbox:
            if {"name": t.name} not in toolbox:
                toolbox.append({"name": t.name})
            if t.thumbnail and not os.path.isfile(os.path.join(toolpath, t.name)):
                t.image.save(os.path.join(toolpath, t.name), "JPEG")
        for i, step in enumerate(doc.steps):
            if step.text_raw not in annotated_steps:
                annotated_steps.add(step.text_raw)
                if step.image and not os.path.isfile(
                        os.path.join(steppath, str(step.stepid))) and image_save(step.image):
                    image_save(step.image).save(os.path.join(steppath, str(step.stepid)), "JPEG")
    cursor.close()


def image_save(stepimg):
    """Combine multiple images for a single step"""
    img = None
    if len(stepimg) > 1:
        ims = []
        for image in stepimg:
            ims.append(image.imagest)
        if ims:
            img = append_images(ims)
        return img
    elif len(stepimg) == 1:
        return stepimg[0].imagest


def find_annotateds(cursor):
    """
    finds all the annotated steps in the category.
    it also searches the database and finds the annotated steps. split the step to the sentences and
    changes the span of objects from the beginning of step to th beginning of sentence.
    :rtype: set, dict
    """
    obj_dic = dict()
    uniques = set()
    annotated_steps = set()
    print('Started finding annotated steps, ...')
    for guid in tqdm(cursor):
        for step in guid.steps:
            if step.wordobject is not None and step.text_raw not in uniques:
                annotated_steps.add(step.text_raw)
                uniques.add(step.text_raw)
                if step.wordobject:
                    sents = step.sentences
                    points = start_points(sents)
                    for ind, sent in enumerate(sents):
                        sent = sent.strip()
                        _tmpo = []
                        _tmpv = []
                        for obj in step.wordobject:
                            if obj.span[0] >= points[ind] and obj.span[1] < points[ind + 1]:
                                obj.span = [i - points[ind] for i in obj.span]
                                _tmpo.append({"name": obj.name, "span": obj.span})
                        if step.verbobject:
                            for verb in step.verbobject:
                                if verb.span[0] >= points[ind] and verb.span[1] < points[ind + 1]:
                                    verb.span = [i - points[ind] for i in verb.span]
                                    _tmpv.append({"name": verb.name, "span": verb.span})
                        if sent not in obj_dic:
                            obj_dic[sent] = (_tmpo, _tmpv)

    # cursor.close()
    print('{} annotated steps are found'.format(len(annotated_steps)))
    return annotated_steps, obj_dic


def start_points(sents):
    """
    Receives a list of sentences and gives the start point (number of words before) of each sentence.
    :rtype: list
    """
    start = 0
    points = []
    for sent in sents:
        points.append(start)
        start += len([i for i in sent.split() if i != '.'])
    points.append(float("inf"))
    return points


def fix_span(dic, p):
    """
    changing the span of words from sentence level to step level
    :rtype: dict
    """
    return {'name': dic['name'], 'span': [i + p for i in dic['span']]}


def basic_extract(sents, extracted, annotateds, non_artifacts):
    """
    Given the verb and object candidates and the description of step, it separates the already annotated
    and not annotated sentences in the step. changes the span of the words from sentence level to step level.
    it also pre-check the checkboxes of the candidates that are selected in previous steps.
    """
    pointer = 0
    objects = []
    verbs = []
    not_wnartifacts = []
    annotated_sentences = dict()
    txt = ''
    for ind, sent in enumerate(sents):
        sent = sent.strip()
        if sent in annotateds:
            annotated_sentences[sent] = (
                [fix_span(i, pointer) for i in annotateds[sent][0]],
                [fix_span(i, pointer) for i in annotateds[sent][1]])
            pointer += len([i for i in sent.split() if i != '.'])
        elif sent in extracted:
            [objects.append(fix_span(i, pointer)) for i in extracted[sent][0]]
            [verbs.append(fix_span(i, pointer)) for i in extracted[sent][1]]
            pointer += len([i for i in sent.split() if i != '.'])
            txt += (sent + ' ')
        if sent in non_artifacts:
            [not_wnartifacts.append(i) for i in non_artifacts[sent]]

    return obj_checked(objects, detachable_objs), obj_checked(verbs,
                                                              detaching_verbs), txt, annotated_sentences, not_wnartifacts


def dbupdate(value, posts, table, field):
    """updating database with the annotation and writing the objects and verbs in the files"""
    if isinstance(value, str):
        value = ast.literal_eval(value)
    res0 = posts.update_one(
        {
            'Guidid': int(table['doc_id']),
            'Steps.StepId': int(table['step_id'])
        },
        {
            "$set": {
                'Steps.$.{}'.format(field): value
            }
        }
    )
    res1 = posts.update_many({'Steps.Text_raw': table['text_raw']},
                             {"$set": {'steps.$.{}'.format(field): value}})

    flash(" {} in {} steps updated with {}".format(field,
                                                   res0.modified_count + res1.modified_count,
                                                   value), 'succes')

    if field == 'Word_level_parts_raw':
        [detachable_objs.add(i['name'].split()[-1]) for i in value]
        with open(detachable_objs_file, 'a+') as file:
            [file.write(i['name'].split()[-1] + '\n') for i in value]
    if field == 'Removal_verbs':
        [detaching_verbs.add(i['name']) for i in value]
        with open(detaching_verbs_file, 'a+') as file:
            [file.write(i['name'] + '\n') for i in value]


def process_annotation(objlis, verblis, obj_indexes, row, dont_use_olds):
    """
    After annotating the step, here we combine the newly annotated sentences with the previously annotated ones.
    it Fixes the object indexes according to the number of selected objects.
    produces two dictionary to be sent into the database,for objects and verbs,
    another dictionary holds the annotated sentences.

    """
    sentdic = dict()
    _objs = []
    _verbs = []
    old_objects = index = new_objects = 0
    words = row['text_raw'].split()
    for i, obj in enumerate(objlis):
        obj, span = obj.split('>')
        objlen = len(obj.split())
        span = span.split('-') if '-' in span else [span, int(span) + objlen - 1]
        if cleantxt(words[int(span[0])]) != cleantxt(obj.split()[0]):
            flash('The words {} and {} dont match'.format(words[int(span[0])].strip(), obj.split()[0].strip()))
            return None, None, None
        _objs.append({"name": obj, "span": [int(j) for j in span]})
    for v, ind in enumerate(obj_indexes):
        verb, vspan = verblis[v].split('>')
        vspan = vspan.split('-') if '-' in vspan else [vspan, vspan]
        if words[int(vspan[0])].lower().strip() != verb.split()[0].lower().strip():
            flash(
                'The words {} and {} dont match'.format(words[int(vspan[0])].lower().strip(), verb.split()[0].strip()))
            return None, None, None
        _verbs.append({"name": verb, "span": [int(j) for j in vspan], "obj_index": ind})

    sents = row['sentences']
    points = start_points(sents)
    step_objects = []
    step_verbs = []

    for ind, sent in enumerate(sents):
        if sent in row['objects_annotation'] and not dont_use_olds:
            for elem in row['objects_annotation'][sent][1]:
                if cleantxt(words[elem['span'][0]]) != cleantxt(elem['name'].split()[0]):
                    flash('The words {} and {} dont match'.format(words[elem['span'][0]].lower().strip(),
                                                                  elem['name'].split()[0].lower().strip()))
                    return None, None, None
                step_verbs.append({"name": elem['name'], "span": elem['span'], "obj_index": index + new_objects})
            for elem in row['objects_annotation'][sent][0]:
                if cleantxt(words[elem['span'][0]]) != cleantxt(elem['name'].split()[0]):
                    flash('The words {} and {} dont match'.format(words[elem['span'][0]].lower().strip(),
                                                                  elem['name'].split()[0].lower().strip()))
                    return None, None, None
                step_objects.append(elem)
                old_objects += 1
                if isinstance(index, list):
                    index = [old_objects + i for i in index]
                else:
                    index += old_objects
        else:
            _sento = []
            _sentv = []
            for obj in _objs:
                if obj['span'][0] >= points[ind] and obj['span'][1] < points[ind + 1]:
                    _tmp = {"name": obj['name'], "span": [i - points[ind] for i in obj['span']]}
                    if cleantxt(words[obj['span'][0]]) != cleantxt(obj['name'].split()[0]):
                        flash('The words {} and {} dont match'.format(words[obj['span'][0]].lower().strip(),
                                                                      obj['name'].split()[0].lower().strip()))
                        return None, None, None
                    step_objects.append(obj)
                    new_objects += 1
                    _sento.append(_tmp)
            for vrb in _verbs:
                if vrb['span'][0] >= points[ind] and vrb['span'][1] < points[ind + 1]:
                    if isinstance(vrb["obj_index"], list):
                        index = [old_objects + i for i in vrb["obj_index"]]
                    else:
                        index = vrb["obj_index"] + old_objects
                    _tmp = {"name": vrb['name'], "span": vrb['span'], "obj_index": index}
                    if cleantxt(words[_tmp['span'][0]]) != cleantxt(_tmp['name'].split()[0]):
                        flash('The words {} and {} dont match'.format(words[_tmp['span'][0]].lower().strip(),
                                                                      _tmp['name'].split()[0].lower().strip()))
                        return None, None, None
                    step_verbs.append(_tmp)
                    _sentv.append({"name": vrb['name'], "span": [i - points[ind] for i in vrb['span']]})
            sentdic[sent] = (_sento, _sentv)
    if dont_use_olds:
        return _objs, _verbs, sentdic
    else:
        return step_objects, step_verbs, sentdic

def add_phrase_head(objs):
    """
    adding the head words to the headless screw types.
    :rtype: str
    """
    ls = []
    for obj in objs:
        _obj = obj[0].split('>')[0].lower().strip()
        if _obj.endswith(headless_objs):
            ls.append(_obj + ' screw')
    return ','.join(ls)

def update_table(table, indx, newsents):
    """
    updating the table of data that website reads from it, with the new annotation
    :rtype: list
    """
    for i in range(len(table[indx:])):
        anns = dict()
        pointer = 0
        txt = []
        dic = table[indx + i]
        for obj in dic['non_artifacts']:
            if obj.split('>')[0].split()[-1] in detachable_objs:
                table[indx + i]['objects'].append((obj, 'checked'))
                table[indx + i]['non_artifacts'].remove(obj)

        for ind, sent in enumerate(sent_tokenize(dic['description'])):
            if sent in newsents:
                anns[sent] = (
                    [fix_span(i, pointer) for i in newsents[sent][0]],
                    [fix_span(i, pointer) for i in newsents[sent][1]])
            else:
                txt.append(sent)
            pointer += len([i for i in sent.split() if i != '.'])
        table[indx + i]['objects_annotation'] = {**dic['objects_annotation'], **anns}
        table[indx + i]['description'] = ' '.join(txt)
    return table


def category_reader():
    """
    reading the category of devices and stats from cat.csv
    :rtype: list
    """
    cat_list = []
    with open(cat_stats) as file:
        csvfile = file.readlines()
    names = csvfile[0].split(',')
    for raw in csvfile[1:]:
        _tmp = {names[i].strip(): j.strip() for i, j in enumerate(raw.split(','))}
        cat_list.append(_tmp)
    return cat_list


def add_word_objects(step_objs, word_objs):
    """
    Adding the word level objects to the step level ones.
    :rtype: list
    """
    step_objs = set(step_objs.split(','))
    for obj in word_objs:
        obj = obj.split('>')[0].strip().lower()
        if obj and not obj.endswith(headless_objs) and not b_any(obj in x for x in step_objs):
            step_objs.add(obj)
    return list(step_objs)
