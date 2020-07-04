#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MyFixit annotator
import math
import os
import re
from collections import Counter, defaultdict
from itertools import chain

import inflect
from nltk.util import ngrams

inflect = inflect.engine()


class Nlps(object):

    def __init__(self):
        self.re_sent_ends_naive = re.compile(r' *[.?!][\'")\]]* +')
        self.re_stripper_naive = re.compile('[^\w+.\n\-]')
        self.splitter_naive = lambda x: self.re_sent_ends_naive.split(self.re_stripper_naive.sub(' ', x))
        script_dir = os.path.dirname(__file__)
        self.stop_words = set(line.strip() for line in open(os.path.join(script_dir, 'stopwords.txt')))  # stopwords
        self.unistops = set(
            line.strip() for line in open(os.path.join(script_dir, 'unigramstops.txt')))  # tools stopword

    @staticmethod
    def jaccard_distance(a, b):
        """Calculate the jaccard distance between sets A and B"""
        a = set(a)
        b = set(b)
        return 1.0 * len(a & b) / len(a | b)

    @staticmethod
    def cosine_similarity_ngrams(a, b):
        """Calculate the cosine similarity between sets A and B"""
        vec1 = Counter(a)
        vec2 = Counter(b)

        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
        sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def stems(self, txt):
        """return the singularized words if not in stoplist"""
        return [self.singular(j) for j in txt if j not in self.stop_words]

    def ngram_compare(self, toolbox, step):
        """
        taking the step text and tool text and return tool freq dist
        """
        if isinstance(toolbox[0], list):
            toolbox = [i[0] for i in toolbox]
        scoredic = {}
        bon = defaultdict(int)
        # sentences in steps
        sentences = tuple(self.stems(x.split()) for x in self.splitter_naive(step) if x)
        for tool in toolbox:
            toolwordlis = [self.singular(w) for w in tool.split()]
            # removing unigram misleading words
            toolwordlis = [w for w in toolwordlis if w not in self.unistops]
            tot = comp = 0
            for i, order in enumerate(range(len(toolwordlis), 0, -1)):
                n = 0
                stepngrams = self.get_tuples_manual_sentences(sentences, order)
                toolngrams = self.get_lists_nosentences(toolwordlis, order)
                bon[tool] += len(toolngrams)
                if stepngrams:
                    commons = [elem for elem in stepngrams if elem in toolngrams]  # common ngrams
                    n = len(commons)
                tot += n
            scoredic[tool] = tot
        return scoredic

    def ngram_simscore(self, text1, text2):
        """
        Calculates the similarity score between two text
        :rtype: int
        """
        n = max(len(text1), len(text2))
        score = 0
        for i in range(n):
            seq1tupes = self.get_tuples_nosentences(text1, i + 1)
            seq2tupes = self.get_tuples_nosentences(text2, i + 1)
            score += ((i + 1) * (len(seq1tupes & seq2tupes)))
        return score

    @staticmethod
    def get_lists_nosentences(txt, n):
        """Get lists that ignores all punctuation (including sentences)."""
        if not txt:
            return None
        ng = ngrams(txt, n)
        return list(ng)

    @staticmethod
    def get_tuples_nosentences(txt, n):
        """Get tuples that ignores all punctuation (including sentences)."""
        if not txt:
            return None
        ng = ngrams(txt, n)
        return set(ng)

    @staticmethod
    def get_tuples_manual_sentences(sentences, n):
        """Naive get tuples that uses periods or newlines to denote sentences."""
        if not sentences:
            return None
        # sentences = (self.lemmaz(x) for x in self.splitter_naive(txt) if x)
        ng = (ngrams(x, n) for x in sentences if len(x) >= n)
        return list(chain(*ng))

    @staticmethod
    def singular(word):
        """
        Returns a singularized word
        :rtype: str
        """
        head = inflect.singular_noun(word)
        if not head:
            head = word
        return head
