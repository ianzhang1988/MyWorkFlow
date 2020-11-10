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
class TaskState(Enum):
    Waiting  = 1
    Finished = 2
    Error    = 3
    Killed   = 4

class EventType:
    NODE="node"
    TASK="task"

# ---------- error -----------

class FlowError(Exception):
    def __init__(self, error_msg, flow_id, node_id=None, task_id=None):
        super(FlowError, self).__init__(error_msg)
        self.flow_id = flow_id
        self.type = "flow"

        if node_id:
            self.node_id = node_id
            self.type = "node"

        if task_id:
            self.task_id = task_id
            self.type = "task"
