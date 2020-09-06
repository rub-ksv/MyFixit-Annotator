#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Automatically extracting the removed objects from text
#


import logging

from flair.data import Sentence
from flair.models import SequenceTagger
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from tqdm import tqdm

from src.part_extraction.sequence_labeling import train_ner, create_column_corpus, clean_puncs
from src.web_app.constants import *
from src.web_app.utils import Guide, docselect, fix_span


class AutoObject(object):
    def __init__(self, posts, device_category, deeporbasic):
        if deeporbasic == 'deep':
            if os.path.isfile('{}{}.pt'.format(ner_models, device_category)):
                logging.info("BILSTM_CRF Loaded from existing model")
                self.model = SequenceTagger.load('{}{}.pt'.format(ner_models, device_category))

            else:
                print("Sequence labeling model does not exist, training a new one")
                if os.path.isfile(os.path.join(root_path, 'part_extraction/data/{}.conll'.format(device_category))):
                    logging.info("Loading column corpus from: \n{}".format(
                        os.path.join(root_path, 'part_extraction/data/{}.conll'.format(device_category))))
                    train_ner(device_category)
                    self.model = SequenceTagger.load('{}{}.pt'.format(ner_models, device_category))

                else:
                    print("Column corpus does not exist, creating a new one")
                    create_column_corpus(posts, device_category)
                    print("training the sequence labeling model")
                    train_ner(device_category)
                    self.model = SequenceTagger.load('{}{}.pt'.format(ner_models, device_category))

    def extract(self, step, annotateds):
        """
        Extracting the object and verb candidates using the bilstm-crf sequence tagging
        """
        sentence = Sentence(step.text_raw)
        self.model.predict(sentence)
        tokens = sentence.tokens
        verbs = []
        objects = []
        _tmpobj = _tmpverb = ''
        _objspan = []
        _verbspan = []
        for ind in range(len(tokens)):
            tag = tokens[ind].get_tag('ner').value
            if tag.endswith('obj'):
                _tmpobj += tokens[ind].text + ' '
                _objspan.append(ind)
            if tag == 'B-verb':
                _tmpverb += tokens[ind].text + ' '
                _verbspan.append(ind)
                for j in range(ind + 1, min(ind + 10, len(tokens))):
                    if tokens[j].get_tag('ner').value == 'E-verb':
                        _tmpverb += tokens[j].text
                        break
                    elif tokens[j].get_tag('ner').value == 'B-verb':
                        break
            if tag == 'O' or tokens[ind].text.endswith((".", ",", "!", ";", "?", ":")):
                if _tmpobj:
                    objects.append(('{} > {}-{}'.format(_tmpobj, _objspan[0], _objspan[-1]), 'checked'))
                    _objspan = []
                    _tmpobj = ''
                if _tmpverb:
                    verbs.append(('{} > {}-{}'.format(_tmpverb, _verbspan[0], _verbspan[-1]), 'checked'))
                    _verbspan = []
                    _tmpverb = ''
        not_annotateds, annotated_sents = self._seperate_annotated(step.sentences, annotateds)
        return objects, verbs, not_annotateds, annotated_sents, []

    def codidates_basic(self, posts, device_category, annotateds):
        print('extracting basic candidates')
        """
        Given the category of device, it extract object candidates from text, if the text is not
        previously annotated.
        The candidates are noun and verb phrases after Wordnet filtering.

        """
        tagger = SequenceTagger.load('chunk')
        extracted = dict()
        non_artifacts_dict = dict()
        cursor = docselect(posts, device_category)
        print('Started extracting basic candidates, ...')
        for d in tqdm(cursor):
            guid = Guide(d)
            for step in guid.steps:
                sents = step.sentences
                for sent in sents:
                    sent = sent.strip()
                    if sent not in extracted and sent not in annotateds:
                        artifacts = []
                        non_artifacts = []
                        verbs = []
                        sentence = Sentence(sent)
                        tagger.predict(sentence)
                        tokens = sentence.tokens
                        last_phrase_start = -1
                        tokens = [tok for tok in tokens if tok.text not in puncs]
                        for ind in range(len(tokens)):
                            otmp = vtmp = None
                            tag = tokens[ind].get_tag('np').value
                            if tag == 'E-NP':
                                for j in range(ind - 1, last_phrase_start, -1):
                                    if tokens[j].get_tag('np').value == 'B-NP':
                                        if tokens[j].text.lower().strip() in bad_nouns:
                                            _ind = j + 1
                                        else:
                                            _ind = j
                                        ws = [clean_puncs(i.text) for i in tokens[_ind:ind + 1] if
                                              i.text not in bad_nouns]
                                        if ws:
                                            otmp = {'name': ' '.join(ws), 'span': [_ind, ind]}
                                        last_phrase_start = ind
                                        break
                            if tag == 'S-NP':
                                otmp = {'name': clean_puncs(tokens[ind].text), 'span': [ind, ind]}

                                last_phrase_start = ind
                            if otmp:
                                if self.is_artifact(tokens[ind].text):
                                    artifacts.append(otmp)
                                else:
                                    non_artifacts.append(tokens[ind].text)

                            if tag == 'E-VP':
                                pind = ind
                                vtmp = tokens[ind].text
                                for k in range(ind, min(len(tokens), ind + search_length), 1):
                                    if tokens[k].get_tag('np').value == 'S-PRT' or \
                                            tokens[k].text.strip().lower() in verb_particles:
                                        vtmp = vtmp + ' ' + tokens[k].text
                                        pind = k
                                        break
                                vtmp = {'name': vtmp, 'span': [ind, pind]}
                            if tag == 'S-VP':
                                vtmp = tokens[ind].text
                                pind = ind
                                for j in range(ind, min(len(tokens), ind + search_length), 1):
                                    if tokens[j].get_tag('np').value == 'S-PRT' or \
                                            tokens[j].text.strip().lower() in verb_particles:
                                        if vtmp:
                                            vtmp = vtmp + ' ' + tokens[j].text
                                        pind = j
                                        break
                                    # if tokens[j].get_tag('np').value.endswith('VP'): break
                                pind = pind if pind == (ind + 1) else ind
                                vtmp = {'name': vtmp, 'span': [ind, pind]}
                            if vtmp:
                                verbs.append(vtmp)
                        extracted[sent] = (artifacts, verbs)
                        non_artifacts_dict[sent] = non_artifacts
        print('Extracting basic candidates ended')
        return extracted, non_artifacts_dict

    @staticmethod
    def _seperate_annotated(sents, annotateds):
        """
        separating annotated sentences from unannotated ones

        """
        pointer = 0
        annotated_sentences = dict()
        not_annotated = ''
        for ind, sent in enumerate(sents):
            sent = sent.strip()
            if sent in annotateds:
                annotated_sentences[sent] = (
                    [fix_span(i, pointer) for i in annotateds[sent][0]],
                    [fix_span(i, pointer) for i in annotateds[sent][1]])
                pointer += len([i for i in sent.split() if i != '.'])
            else:
                pointer += len([i for i in sent.split() if i != '.'])
                not_annotated += (sent + ' ')
        return not_annotated, annotated_sentences

    @staticmethod
    def is_artifact(head):
        """
        Checks if the object is an artifact in Wordnet, or in the list of detachable objects
        """
        if head in detachable_objs:
            return True
        wnl = WordNetLemmatizer()
        lhead = wnl.lemmatize(head, 'n')
        syns = wn.synsets(lhead, pos='n')
        hyps = {i[0].lemma_names()[0] for j in syns for i in j.hypernym_distances()}
        if 'artifact' in hyps:
            return True
        else:
            return False
