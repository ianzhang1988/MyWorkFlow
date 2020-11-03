# -*- coding: utf-8 -*-
# @Time    : 2020/10/26 16:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import time

from myflow.globalvar import db_session_maker
from myflow.workflow import dummy_flow
from myflow.flowengine.dao import FlowDao, init_database, DatabaseFacade
from myflow.flowengine.event_utlity import EventFacade
from myflow.flowengine.engine import Engine

from myflow.flowengine.consts import EventType

init_database()

flow_config = dummy_flow.get_flow_configration()

flow = flow_config.new()
input = {"value":0}
flow.set_input_data(input)
flow_dao = FlowDao(flow, db_session_maker)
flow_id, start_node_id = flow_dao.create()

print('----- flow_id', flow_id,"start_node_id",start_node_id)

# event
event = {
    "flow_name":"dummy",
    "type": EventType.NODE,
    "flow_id":flow_id,
    "node_id":start_node_id,
}

event_facade = EventFacade('10.19.17.188', 5673)
event_facade.connect()
event_facade.send_node_event(event)
db_facade = DatabaseFacade()
engine = Engine(db_facade, event_facade)
engine.register_flow(flow_config.name, flow_config)

engine.run(lambda : db_facade.init_session() )

for _ in range(1000):
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        break

engine.stop()