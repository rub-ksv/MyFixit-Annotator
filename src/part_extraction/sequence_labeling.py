#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Sequence labeling
import os
import re

from flair.datasets import ColumnCorpus
from flair.embeddings import WordEmbeddings, FlairEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

from src.web_app.constants import root_path, ner_models
from src.web_app.utils import puncs, docselect, Guide, verb_particles


def train_ner(device_category):
    """
    Training the sequence labeling model
    """
    columns = {0: 'text', 1: 'ner'}

    training_file = os.path.join(root_path, 'part_extraction/data/{}.conll'.format(device_category))
    data_folder = os.path.join(root_path, 'part_extraction/data')

    corpus = ColumnCorpus(data_folder, columns, train_file=training_file)

    print(len(corpus.train))
    tag_type = 'ner'
    tag_dictionary = corpus.make_tag_dictionary(tag_type=tag_type)
    print(tag_dictionary.idx2item)

    embedding_types = [

        WordEmbeddings('glove'),

        # comment in this line to use character embeddings
        # CharacterEmbeddings(),

        FlairEmbeddings('news-forward'),
        FlairEmbeddings('news-backward'),
    ]

    embeddings = StackedEmbeddings(embeddings=embedding_types)

    tagger = SequenceTagger(hidden_size=256, embeddings=embeddings, tag_dictionary=tag_dictionary, tag_type=tag_type,
                            use_crf=True)

    trainer = ModelTrainer(tagger, corpus)

    # 7. start training
    trainer.train(ner_models,
                  learning_rate=0.1,
                  mini_batch_size=32,
                  max_epochs=150)

    trainer.model.save('{}/{}.pt'.format(ner_models, device_category))


def create_raws(tokens, ind, inp, file=None):
    """
    Receives the token, the index of the token in the sentence, the sentences in the step and the labels,
    produces a raw in column corpus
    :rtype: str
    """
    ref = tokens[ind]
    txt, lab = inp
    txt = re.sub(r'[^\'\w+.!,();/:?-]', '', txt)
    if 'http' in txt:
        return True

    if ref.endswith(puncs):
        txt_towrite = ref[:-1] + '\t' + lab + '\n' + ref[-1] + '\t' + 'O' + '\n'
    else:
        txt_towrite = ref + '\t' + lab + '\n'
    file.write(txt_towrite)


def clean_puncs(txt):
    """
    removes the punctuation sticked to the words
    :rtype: str
    """
    if txt.endswith(puncs):
        txt = txt[:-1]
    if txt.startswith(puncs):
        txt = txt[1:]
    return txt.lower().strip()


def create_column_corpus(posts, device_category):
    """
    Searching in the debase given the device category, selecting the steps with unique texts, and writing the column
    corpus
    :rtype: None
    """
    datapth = os.path.join(root_path, 'part_extraction/data/{}.conll'.format(device_category))
    if not os.path.exists(os.path.join(root_path, 'part_extraction/data/')):
        os.makedirs(os.path.join(root_path, 'part_extraction/data/'))
    file = open(datapth, 'w')
    cursor = docselect(posts, device_category)
    uniques = set()
    for d in cursor:
        guid = Guide(d)
        for step in guid.steps:
            if step.wordobject and step.text_raw not in uniques:
                uniques.add(step.text_raw)
                tokens = step.text_raw.split()
                obj_spans = dict()
                verb_spans = dict()

                for obj in step.wordobject:
                    obj_len = len(obj.name.split())
                    if obj_len > 1:
                        obj_labels = ['I-part'] * obj_len
                        obj_labels[-1] = 'E-part'
                        obj_labels[0] = 'B-part'
                    else:
                        obj_labels = ['B-part']
                    wordind = 0
                    for span, word in zip(range(obj.span[0], obj.span[1] + 1), obj.name.split()):
                        obj_spans[span] = (word, obj_labels[wordind])
                        wordind += 1

                for verb in step.verbobject:
                    verblen = len(verb.name.split())
                    if verblen == 1:
                        verb_spans[verb.span[1]] = (verb.name, 'B-verb')

                    else:
                        verb_spans[verb.span[1]] = (verb.name.split()[0], 'B-verb') if verb.name.split()[
                                                                                           0] != 'to' else (
                            verb.name.split()[1], 'B-verb')
                        for ind in range(verb.span[0], min(verb.span[0] + 10, len(tokens))):
                            if clean_puncs(tokens[ind]) in verb_particles:
                                verb_spans[ind] = (tokens[ind], 'E-verb')
                                break

                for ind, tok in enumerate(tokens):
                    if ind in obj_spans:
                        create_raws(tokens, ind, obj_spans[ind], file)
                    elif ind in verb_spans:
                        create_raws(tokens, ind, verb_spans[ind], file)
                    else:
                        create_raws(tokens, ind, (tok, 'O'), file)
                file.write('\n\n')
    file.close()


# if __name__ == '__main__':
# posts = start_db(address=mongo_address)
# # create_column_corpus(posts,device_category, '/part_extraction/data/tmp.conll')
# train_ner('tmp')
