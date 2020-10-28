# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:38
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from myflow.flowengine.consts import State

class Flow:
    def __init__(self):
        self.name = ""
        self.job_id = ""
        # self.description = ""
        self.input_data=None
        self.state = State.PENDING

    def set_input_data(self, input_data):
        self.input_data = input_data

class FlowConfigration(Flow):
    def __init__(self):
        super().__init__()

        self.nodes = {} # num: node
        self.node_id_generator = 0

    def add_node(self, node):
        self.node_id_generator += 1

        node.set_node_num(self.node_id_generator)
        self.nodes[self.node_id_generator] = node

    def connect_node(self, src, dst):
        self.nodes[src].connect(self.nodes[dst])

