# -*- coding: utf-8 -*-
# @Time    : 2020/10/26 15:57
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com


from myflow.flowengine.flow import Flow, FlowConfigration
from myflow.flowengine.node import Node, Start, End, TaskNode
from myflow.flowengine.consts import State

class First(Start):

    def work(self):
        data = self._get_input_data()

        out_data = {}
        out_data["value"] = data["value"] + 1

        if "list" in data:
            out_data["list"] = data["list"]

        self.work_data = out_data
        self.user_data={"msg":"1st done"}
        print("First")

        self.state = State.SUCCESS

        return self.work_data


class Second(Node):
    def work(self):
        data = self._get_node_data(First.__name__)

        out_data = {}
        out_data["value"] = data["value"] + 1

        self.work_data = out_data
        self.user_data = {"msg":"2nd done"}
        print("Second")

        self.state = State.SUCCESS

        return self.work_data

class Third(End):
    def work(self):
        data = self._get_node_data(Second.__name__)
        double_data = self._get_node_data(Double.__name__)

        out_data = {}
        out_data["value"] = data["value"] + 1

        self.work_data = out_data
        self.user_data = {"msg":"3rd done"}
        print("Third")

        if double_data:
            self.work_data["list"] = double_data["list"]

        self.state = State.SUCCESS

        return self.work_data

class Double(TaskNode):
    def generate_task(self):
        data = self._get_node_data(First.__name__)
        number_list = data["list"]
        for idx, num in enumerate(number_list):
            task = self._new_task(idx)
            task.input_data["value"] = num
            self.add_task(task)

    def gather_task(self):
        doubled_number = []
        for t in self.tasks:
            doubled_number.append(t.work_data["value"])
        self.work_data["list"] = doubled_number

        self.state = State.SUCCESS

def get_flow_configration():

    f = FlowConfigration()

    f.name="dummy"

    f.add_node(First())  #1
    f.add_node(Second()) #2
    f.add_node(Third())  #3
    f.add_node(Double()) #4


    f.connect_node(1,2)
    f.connect_node(2,3)
    f.connect_node(1,4)
    f.connect_node(4,3)

    return f

if __name__ == "__main__":
    f = get_flow_configration()