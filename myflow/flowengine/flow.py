# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:38
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

class Flow:
    def __init__(self):
        self.nodes = {} # num: node
        self.node_id_generator = 0

        self.name = ""
        # self.description = ""

    def add_node(self, node):
        self.node_id_generator += 1

        node.set_id(self.node_id_generator)
        self.nodes[self.node_id_generator] = node

    def connect_node(self, src, dst):
        self.nodes[src].connect(self.nodes[dst])

    def save(self):
        # save flow to database
        keys = sorted(list(self.nodes.keys()))

        # transaction

        for k in keys:

            self.nodes

    def node_work(self, node_id):
        self.nodes[node_id].work()