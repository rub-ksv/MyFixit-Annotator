#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Automatic extraction of objects
import logging
import random
from flask import Flask, render_template, request, redirect
from src.part_extraction.autoobject import AutoObject
from src.tool_extraction.autotool import AutoTool
from src.web_app.pager import Pager
from src.pyfixit import Guide
from src.web_app.utils import *

logging.basicConfig(level = logging.INFO)
app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path=STATIC_FOLDER)
app.config.update(
    APPNAME=APPNAME,
    SECRET_KEY='development',
)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
posts = start_db(address=mongo_address)
table = []
pager = Pager(len(table))
deep_or_basic = 'basic'


def runner():
    """
    Starting the app.
    """
    app.run(host='0.0.0.0', debug=True)


def creat_table(category):

    """Receives the category of devices, queries database and generates a list of dicts for steps.
    It also downloads the images of each tool and step in a local folder.
    :rtype: list
    """
    toolpath, steppath = check_statics()
    tablepath = os.path.join(STATIC_FOLDER, 'tables')
    if not os.path.exists(tablepath):
        os.makedirs(tablepath)

    tab = []

    cursor = docselect(posts, category)
    guids = [Guide(d, noimage=False) for d in cursor]

    # categories = category_reader()
    # for cat in categories[1:]:
    #     category = cat['Category']
    #     print('Selected category:', category)
    #     cursor = list(docselect(posts, category))
    #     random.Random(4).shuffle(cursor)
    #     guids = [Guide(d, noimage=False) for d in cursor[:20]]
    annotated_steps, annotated_sents = find_annotateds(guids)
    object_extractor = AutoObject(guids, category, deep_or_basic)
    if deep_or_basic == 'basic':
        sentence_candidates, wn_not_artifacts = object_extractor.codidates_basic(guids, annotated_sents)

    tool_extractor = AutoTool(guids)


    print("start creating the tables")
    for counter, doc in enumerate(guids):
        # doc = Guide(d, noimage=False)
        toolbox = []
        for t in doc.toolbox:
            if {"name": t.name} not in toolbox:
                toolbox.append({"name": t.name})
            if t.thumbnail and not os.path.isfile(os.path.join(toolpath, t.name)):
                t.image.save(os.path.join(toolpath, t.name), "JPEG")
        toolbox.append({"name": 'no tool'})

        for i, step in enumerate(doc.steps):
            if (not step.wordobject) and (
                    step.text_raw not in annotated_steps):
                annotated_steps.add(step.text_raw)
                if deep_or_basic == 'deep':
                    objs, verbs, txt, objects_annotation, new_not_artifacts = object_extractor.extract(step,
                                                                                                       annotated_sents)
                else:
                    objs, verbs, txt, objects_annotation, new_not_artifacts = basic_extract(step.sentences,
                                                                                            sentence_candidates,
                                                                                            annotated_sents,
                                                                                            wn_not_artifacts)
                tool_prediction = tool_extractor.extract(step, [t['name'] for t in toolbox[:-1]])
                dictowrite = {'name': doc.title,
                              'description': txt,
                              'with_number': ' '.join(
                                  ["({} {})".format(j, i) for i, j in
                                   enumerate(step.text_raw.split())]),
                              'order': "{} of {}".format(i + 1, len(doc.steps)),
                              'toolbox': tools_checked(toolbox, tool_prediction),
                              'step_id': str(step.stepid),
                              'tool_prediction': tool_prediction,
                              'sentences': step.sentences,
                              'non_artifacts': new_not_artifacts,
                              'objects_annotation': objects_annotation,
                              'tools_annotation': step.tools_annotation,
                              'objects': objs,
                              'text_clean': step.text_clean,
                              'text_raw': step.text_raw,
                              'doc_id': step.guideid,
                              'url': doc.url,
                              'verb': verbs,
                              'stepobj': add_phrase_head(objs),
                              'ancestors': doc.ancestors}
                tab.append(dictowrite)
                if step.image and not os.path.isfile(
                        os.path.join(steppath, str(step.stepid))) and image_save(step.image):
                    image_save(step.image).save(os.path.join(steppath, str(step.stepid)), "JPEG")

    print('Total steps: {}'.format(len(tab)))
    if len(tab) > 0:
        save_obj(tab, os.path.join(STATIC_FOLDER, 'tables/{}_{}'.format(categ, deep_or_basic)))
    else:
        logging.error(
            'We could not find any manual that match the input.\n Please check if you have loaded the right '
            'category into the database',
            'error')
    # cursor.close()
    return tab


@app.route('/')
def index():
    """
    front page
    """
    categories = category_reader()
    return render_template("selection.html", cats=categories)


@app.route('/<int:ind>/')
def step_view(ind=None):
    """
    Loading a step's annotation page.
    """
    if ind >= pager.count:
        return render_template("404.html"), 404
    else:
        pager.current = ind
        global indx
        indx = ind
        return render_template(
            'stepview.html',
            index=ind,
            pager=pager,
            data=table[ind])


@app.route('/whensubmit', methods=['POST'])
def submitting():
    """
    After pressing the submit button, here the annotation is processed and database will be updated.
    """
    global table
    try:
        tools = request.form.getlist("tools")
        tools = [i for i in tools if len(i) > 0]
        if tools and ',' in tools[-1]:
            _tmp = tools.pop(-1)
            [tools.append(i) for i in _tmp.split(',')]

        word_objs = request.form.getlist("word_objs")
        word_objs = [i for i in word_objs if len(i) > 0]
        if word_objs and ',' in word_objs[-1]:
            _tmp = word_objs.pop(-1)
            [word_objs.append(i) for i in _tmp.split(',')]
        verbs = request.form.getlist("verb")
        verbs = [i for i in verbs if len(i) > 0]
        if verbs and ',' in verbs[-1]:
            _tmp = verbs.pop(-1)
            [verbs.append(i) for i in _tmp.split(',')]
        inds = request.form.get("indexes")
        step_objs = request.form.get("step_objs")
        dont_use_olds = request.form.get("use_olds")

        if verbs and len(verbs) != len(word_objs) or len(inds) > 0:
            if inds:
                inds = inds.split(',')
                obj_indexed = []
                if len(inds) == len(verbs):
                    for _ind in inds:
                        if '&' in _ind:
                            _ind = [int(i) - 1 for i in _ind.split('&')]
                            obj_indexed.append(_ind)
                        else:
                            obj_indexed.append(int(_ind) - 1)
                else:
                    flash('The number of verbs and indexes should be equal. please try again', 'error')
                    return redirect('/' + str(pager.current))
            else:
                flash('Please enter the verb indexes', 'error')
                return redirect('/' + str(pager.current))
        elif verbs:
            obj_indexed = [i for i in range(len(verbs))]
        else:
            obj_indexed = []

        objsdic, verbsdic, new_sents = process_annotation(word_objs, verbs, obj_indexed, table[indx], dont_use_olds)
        if objsdic is None:
            flash('Selected span does not match the selected word', 'error')
            return redirect('/' + str(pager.current))
    except Exception as e:
        flash(str(e) + '\n' + 'Something went wrong, Please check the inputs and try again', 'error')
        return redirect('/' + str(pager.current))

    dbupdate(objsdic, posts, table[indx], 'Word_level_parts_raw')
    dbupdate(tools, posts, table[indx], 'Tools_annotated')
    if len(step_objs) > 1:
        dbupdate(add_word_objects(step_objs, word_objs), posts, table[indx], 'Step_level_parts')
    dbupdate(verbsdic, posts, table[indx], 'Removal_verbs')

    table = update_table(table, indx, new_sents)

    return redirect('/' + str(pager.next))


@app.route('/goto', methods=['POST', 'GET'])
def goto():
    return redirect('/' + request.form['index'])


@app.route('/cat_select', methods=['POST'])
def cat_select():
    """
    After selecting the category, the table is built/loaded here.
    """
    global table, pager, device_category, deep_or_basic
    deep = request.form.get("deep")
    if deep:
        deep_or_basic = 'deep'
    only_images = request.form.get("images")
    device_category = request.form.get("cat")
    if os.path.isfile(os.path.join(STATIC_FOLDER, 'tables/{}_{}.pkl'.format(device_category, deep_or_basic))):
        flash("Loaded from existing table: \n{}".format(
            os.path.join(STATIC_FOLDER, 'tables/{}_{}.pkl'.format(device_category, deep_or_basic))))
        table = load_obj(os.path.join(STATIC_FOLDER, 'tables/{}_{}'.format(device_category, deep_or_basic)))
        logging.info('Downloading images for the steps and tools in the category {}.'.format(device_category))
        if only_images:
            download_images(posts, device_category)
    else:
        logging.info(
            'The processed data for the category {} is not found.\n Generating the data, please be patient...'.format(
                device_category))
        table = creat_table(device_category)
    pager = Pager(len(table))
    return redirect('/0')


if __name__ == '__main__':

    # app.run(host='0.0.0.0', debug=True)
    creat_table('ALL20')
