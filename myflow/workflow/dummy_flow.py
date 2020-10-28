# -*- coding: utf-8 -*-
# @Time    : 2020/10/26 15:57
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com


from myflow.flowengine.flow import Flow, FlowConfigration
from myflow.flowengine.node import Node, Start, End

class First(Start):
    def __init__(self):
        super().__init__()

    def work(self):
        print("First")


class Second(Node):
    def work(self):
        print("Second")

class Third(End):
    def work(self):
        print("Third")

def get_flow_configration():

    f = FlowConfigration()

    f.add_node(First())  #1
    f.add_node(Second()) #2
    f.add_node(Third())  #3

    f.connect_node(1,2)
    f.connect_node(2,3)

    return f