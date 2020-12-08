# -*- coding: utf-8 -*-
# @Time    : 2020/10/26 16:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import time
import logging

import sys
sys.path.append("..")

from myflow.globalvar import db_session_maker
from myflow.workflow import dummy_flow
from myflow.flowengine.dao import FlowDao, init_database, DatabaseFacade
from myflow.flowengine.event_utlity import EventFacade, OutBox
from myflow.flowengine.engine import Engine

from myflow.flowengine.consts import EventType
from myflow.dummy_worker import Worker

from myflow.Utility.myprofiler import output_profile

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')


init_database()

flow_config = dummy_flow.get_flow_configration()

flow = flow_config.new()
input = {"value":0, "list": [1,2,3,4,5]}
flow.set_input_data(input)
flow_dao = FlowDao(flow, db_session_maker)
flow_id, start_node_id = flow_dao.create()

print('----- flow_id', flow_id,"start_node_id",start_node_id)


worker = Worker()
worker.start()

# event
event = {
    "flow_name":"dummy",
    "type": EventType.NODE,
    "flow_id":flow_id,
    "node_id":start_node_id,
}

import threading
t = threading.currentThread()
print('main Thread id : %d  name : %s' % (t.ident, t.getName()))

event_facade2 = EventFacade('10.19.17.188', 5673)
event_facade2.connect()
event_facade2.send_node_event(event)
event_facade2.connection.process_data_events()

outbox = OutBox('10.19.17.188', 5673)
outbox.start()
event_facade = EventFacade('10.19.17.188', 5673)
# event_facade.start_dummy_event()
# event_facade.send_node_event(event)
db_facade = DatabaseFacade()
engine = Engine(db_facade, event_facade)
engine.register_flow(flow_config.name, flow_config)

engine.run()

print("after engine run")

for _ in range(1000):
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        break

output_profile(output_file="one_step.1000.prof", sort_by='cumulative', lines_to_print=30)

outbox.stop()
worker.stop()
engine.stop()

worker.join()
