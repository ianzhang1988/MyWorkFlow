# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:39
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from myflow.flowengine.consts import State

class Node:
    def __init__(self):
        self.input_nodes = []
        self.output_nodes = []

        self.node_num = None

        self.work_data = None
        self.user_data = None

        self.state = State.PENDING

        self.create_date = None
        self.finish_date = None

    def set_node_num(self, id):
        self.node_num = id

    def connect(self, other):
        self.output_nodes.append(other)
        other.input_nodes.append(self)

    def input_node_string(self):
        return ",".join(map(lambda x : str(x.node_num), self.input_nodes))

    def output_node_string(self):
        return ",".join(map(lambda x : str(x.node_num), self.output_nodes))

    def work(self):
        pass


class Start(Node):
    pass

class End(Node):
    pass