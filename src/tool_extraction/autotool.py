#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Automatic extraction of tools
from src.pyfixit import Guide
from src.tool_extraction.nlps import Nlps
from src.web_app.utils import docselect


class AutoTool(object):
    def __init__(self, posts):
        # doclist = docselect(posts, cat)
        alltools = []
        for doc in posts:
            # doc = Guide(guid)
            cattools = [t.name for t in doc.toolbox]
            [alltools.append(i) for i in cattools]
        self.sorted_tools = sorted(alltools, key=alltools.count, reverse=True)
        self.nlps = Nlps()

    def get_tool(self, prediction):
        """
        receives the dictionary of tool predictions, and check for multi vs single tool.
        for each case the tool or list of tools is returned.
        """
        # TODO: needs to be extended for more than two
        if sum(prediction.values()) == 0:
            return 'no tool'
        else:
            max_score = max(prediction.values())
            tools = [key for key, value in prediction.items() if value == max_score]
            if len(tools) > 1:
                tools1 = tools[0].split()
                tools2 = tools[1].split()
                common = [element for element in tools1 if element in tools2]
                if len(common) > 0:
                    tools = ' '.join(common)
                else:
                    for tool in self.sorted_tools:
                        if tool in tools:
                            return tool
                        else:
                            return tools[0]
                return tools
            else:
                return tools[0]

    def extract(self, step, tools, min_len_for_mutitool=1):
        """returning the required tool of each step by line-by-line comparison"""
        if len(step.lines) > min_len_for_mutitool:
            prediction = set()
            for i, line in enumerate(step.lines):
                score = self.nlps.ngram_compare(tools, line.text)
                tool = self.get_tool(score)
                if tool and tool not in prediction and tool != 'no tool':
                    prediction.add(tool)
            prediction = list(prediction)
            if len(prediction) > 0:
                if len(prediction) > 1:
                    if all(elem in prediction[1].split() for elem in prediction[0].split()):
                        return [prediction[1]]
                    elif all(elem in prediction[0].split() for elem in prediction[1].split()):
                        return [prediction[0]]
                return prediction
            else:
                return ['no tool']
        else:
            score = self.nlps.ngram_compare(tools, step.text_clean)
            tool = self.get_tool(score)
            return [tool]
