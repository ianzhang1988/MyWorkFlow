# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:38
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from myflow.flowengine.consts import State

class Flow:
    def __init__(self):
        self.nodes = {}  # num: node
        self.name = ""
        self.job_id = ""
        # self.description = ""
        self.input_data=None
        self.state = State.PENDING

        self.work_data = None
        self.user_data = None

        self.create_date = None
        self.finish_date = None

        self.id = None

    def set_input_data(self, input_data):
        self.input_data = input_data

class FlowConfigration(Flow):
    def __init__(self):
        super().__init__()
        self.node_id_generator = 0

    def add_node(self, node):
        self.node_id_generator += 1

        node.set_node_num(self.node_id_generator)
        self.nodes[self.node_id_generator] = node

    def connect_node(self, src, dst):
        self.nodes[src].connect(self.nodes[dst])

    def new(self):
        flow = Flow()

        flow.name = self.name

        for n in self.nodes:
            node = self.nodes[n]
            flow.nodes[n] = node.new(node)
        # connect nodes
        for config_node in self.nodes.values():
            new_node = flow.nodes[config_node.node_num]

            for i in config_node.input_nodes:
                new_node.input_nodes.append(flow.nodes[i.node_num])
            for o in config_node.output_nodes:
                new_node.output_nodes.append(flow.nodes[o.node_num])

        return flow

    def new_node(self, node_num):
        node = self.nodes[node_num]
        return node.new(node)



