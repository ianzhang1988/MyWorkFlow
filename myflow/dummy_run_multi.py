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

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')


init_database()

flow_config = dummy_flow.get_flow_configration()

import threading
t = threading.currentThread()
print('main Thread id : %d  name : %s' % (t.ident, t.getName()))

worker_list=[]
for _ in range(2):

    worker = Worker()
    worker_list.append(worker)
    worker.start()


outbox = OutBox('10.19.17.188', 5673)
outbox.start()

engine_list=[]

for _ in range(2):
    event_facade = EventFacade('10.19.17.188', 5673)
    # event_facade.start_dummy_event()
    # event_facade.send_node_event(event)
    db_facade = DatabaseFacade()
    engine = Engine(db_facade, event_facade)
    engine.register_flow(flow_config.name, flow_config)

    engine.run()
    engine_list.append(engine)

print("after engine run")

def generate_flow(num):
    for _ in range(num):
        flow = flow_config.new()
        input = {"value":0, "list": [1,2,3,4,5]}
        flow.set_input_data(input)
        flow_dao = FlowDao(flow, db_session_maker)
        yield flow_dao.create() # flow_id, start_node_id

    # print('----- flow_id', flow_id,"start_node_id",start_node_id)


# event

def send_task():
    event_facade2 = EventFacade('10.19.17.188', 5673)
    event_facade2.connect()

    for flow_id, start_node_id in generate_flow(500):
        event = {
            "flow_name":"dummy",
            "type": EventType.NODE,
            "flow_id":flow_id,
            "node_id":start_node_id,
        }

        event_facade2.send_node_event(event)
        event_facade2.connection.process_data_events()

send_task_threads = []
for _ in range(2):
    send_t = threading.Thread(target=send_task)
    send_task_threads.append(send_t)
    send_t.start()

print("------- event sent -------")

for _ in range(1000):
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        break

print("timeout stop")

outbox.stop()

for engine in engine_list:
    engine.stop()

for worker in worker_list:
    worker.stop()
    worker.join()

for send_t in send_task_threads:
    send_t.join()
