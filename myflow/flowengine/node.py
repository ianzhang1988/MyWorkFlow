# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:39
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from abc import ABC, abstractmethod

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

    def _map_node_name(self):
        for n in self.input_nodes:
            self.input_name2node[n.name] = n

    def _work(self):
        self.state = State.WORKING

        self._map_node_name()

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

        self.input_data = None
        self.work_data = None
        self.user_data = None

        self.create_date = None
        self.finish_date = None

class TaskNode(Node, ABC):
    def __init__(self):
        super(TaskNode, self).__init__()
        self.tasks = {} # task_num : task
        self.task_ready = False
        self.need_send_task = False

    def add_task(self, task):
        self.tasks[task.task_num] = task

    def task_for_send(self):
        if self.need_send_task:
            return self.tasks
        return None

    def check_tasks_ready(self, ready):
        self.task_ready = ready

    @abstractmethod
    def generate_task(self):
        ...

    @abstractmethod
    def gather_task(self):
        ...

    def _work(self):
        data={}

        self._map_node_name()

        if self.state == State.PENDING:
            self.generate_task()
            self.need_send_task = True

        if self.state == State.PENDING:
            self.state = State.WORKING

        if self.task_ready:
            data = self.gather_task()

        # self.state = State.SUCCESS

        return data



# class TaskGroupNode(TaskNode):
#     def __init__(self):
#         super().__init__()
#
