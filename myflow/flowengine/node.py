# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:39
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

class Node:
    def __init__(self):
        self.input_nodes = []
        self.output_nodes = []

        self.node_id = None

        self.work_data = None
        self.user_data = None

        self.state = None

    def set_id(self, id):
        self.node_id = id

    def connect(self, other):
        self.output_nodes.append(other.node_num)
        other.input_nodes.append(self.node_id)

    def input_node_string(self):
        return ",".join(map(str, self.input_nodes))


    def output_node_string(self):
        return ",".join(map(str, self.output_nodes))

    def work(self):
        pass

