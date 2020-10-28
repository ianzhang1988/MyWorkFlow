# -*- coding: utf-8 -*-
# @Time    : 2020/10/26 16:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from myflow.globalvar import db_session_maker, node_event_queue
from myflow.workflow import dummy_flow
from myflow.flowengine.dao import FlowDao, init_database, DatabaseFacade
from myflow.flowengine.engine import Engine

from myflow.flowengine.consts import EventType

init_database()

flow = dummy_flow.get_flow_configration()

flow.set_input_data("test")
flow_dao = FlowDao(flow, db_session_maker)
flow_id, start_node_id = flow_dao.create()

print('----- flow_id', flow_id,"start_node_id",start_node_id)

# event
event = {
    "flow_name":"test",
    "type": EventType.NODE,
    "flow_id":flow_id,
    "node_id":start_node_id,
}

node_event_queue.put(event)

db_facade = DatabaseFacade()
engine = Engine(db_facade)

for _ in range(100):
    if node_event_queue.empty():
        break

    event=node_event_queue.get()
    engine.one_step(event)