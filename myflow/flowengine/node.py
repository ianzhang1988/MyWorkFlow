# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 16:39
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from abc import ABC, abstractmethod

from myflow.flowengine.consts import State, TaskState, FlowError
from datetime import datetime

class Node:
    def __init__(self):
        self.node_num = None
        self.node_name = None

        self.input_nodes = []
        self.output_nodes = []

        self.input_name2node = {}

        self.work_data = {}
        self.user_data = {}

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
        if name not in self.input_name2node:
            return {}
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

        self.input_data = {}
        self.work_data = {}
        self.user_data = {}

        self.create_date = None
        self.finish_date = None

class TaskNode(Node, ABC):
    def __init__(self):
        super(TaskNode, self).__init__()
        self.tasks = {} # task_num : task
        self.task_state = TaskState.Waiting
        self.need_send_task = False

        self._get_tasks_state = None
        self._get_tasks = None

    def add_task(self, task):
        self.tasks[task.task_num] = task

    def task_for_send(self):
        if self.need_send_task:
            return self.tasks.values()
        return None

    def reg_check_tasks_state_call(self, call):
        self._get_tasks_state = call

    def reg_get_tasks_call(self, call):
        self._get_tasks = call

    def _error_handle(self):
        for t in self.tasks:
            if t.state == State.FAILED:
                error = t.work_data.get("error","no error msg")
                raise FlowError(error, self.flow_id, self.id)

    def _new_task(self, task_num):
        task = Task()
        task.task_num = task_num
        task.flow_id = self.flow_id
        task.node_id = self.id
        task.create_date = datetime.now()

        return task


    @abstractmethod
    def generate_task(self):
        ...

    @abstractmethod
    def gather_task(self):
        ...

    def _work(self):
        data={}

        self._map_node_name()

        # State.PENDING
        if self.state == State.PENDING:
            self.generate_task()
            self.need_send_task = True
            self.state = State.WORKING
            return data

        # State.WORKING
        self.task_state = self._get_tasks_state()

        print("&&&&&&& task_state %s", self.task_state)

        if self.task_state == TaskState.Killed:
            # if killed just ignore the task
            return data

        if self.task_state != TaskState.Waiting:
            self._get_tasks()

        if self.task_state == TaskState.Error:
            self._error_handle()

        if self.task_state == TaskState.Finished:
            data = self.gather_task()

        # self.state = State.SUCCESS

        return data



# class TaskGroupNode(TaskNode):
#     def __init__(self):
#         super().__init__()
#
