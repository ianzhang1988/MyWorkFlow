# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:39
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from myflow.flowengine.consts import State

class Node:
    def __init__(self):
        self.node_num = None
        self.node_name = None

        self.input_nodes = []
        self.output_nodes = []

        self.input_name2node = {}

        self.work_data = None
        self.user_data = None

        self.state = State.PENDING

        self.create_date = None
        self.finish_date = None

        self.id = None
        self.flow_id = None

    def set_node_num(self, id):
        self.node_num = id

    def connect(self, other):
        self.output_nodes.append(other)
        other.input_nodes.append(self)

    def input_node_string(self):
        return ",".join(map(lambda x : str(x.node_num), self.input_nodes))

    def output_node_string(self):
        return ",".join(map(lambda x : str(x.node_num), self.output_nodes))

    def _get_node_data(self, name):
        return self.input_name2node[name].work_data

    def _work(self):
        self.state = State.WORKING

        for n in self.input_nodes:
            self.input_name2node[n.name] = n

        data = self.work()

        # self.state = State.SUCCESS

        return data

    def work(self):
        pass

    @classmethod
    def new(cls, node):
        new_node = cls()
        new_node.name = cls.__name__
        new_node.node_num = node.node_num

        return new_node


class Start(Node):
    def __init__(self):
        super().__init__()
        self.input_data = None

    def set_input_data(self, data):
        self.input_data = data

    def _get_input_data(self):
        return self.input_data

class End(Node):
    pass

class Task:
    def __init__(self):
        self.id = None
        self.node_id = None
        self.flow_id = None

        self.task_num = None
        self.state = State.PENDING

        self.work_data = None
        self.user_data = None

        self.create_date = None
        self.finish_date = None

class TaskNode(Node):
    def __init__(self):
        super(TaskNode, self).__init__()
        self.tasks = {} # task_num : task


class TaskGroupNode(TaskNode):
    def __init__(self):
        super().__init__()

