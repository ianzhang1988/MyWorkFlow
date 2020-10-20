# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:39
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

class Node:
    def __init__(self):
        self.inputs = []
        self.outputs = []

        self.node_id = None

    def set_id(self, id):
        self.node_id = id

    def connect(self, other):
        self.outputs.append(other.node_id)
        other.inputs.append(self.node_id)