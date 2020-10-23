# -*- coding: utf-8 -*-
# @Time    : 2020/10/20 12:23
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from enum import Enum, unique

class State:
    PENDING = "pending"
    WORKING = "working"
    KILLED  = "killed"
    FAILED  = "failed"
    SUCCESS = "success"

@unique
class NodeType(Enum):
    Start = 1
    Inter = 2
    End   = 3

