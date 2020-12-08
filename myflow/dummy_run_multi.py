# -*- coding: utf-8 -*-
# @Time    : 2020/10/26 16:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import time
import logging

import sys
sys.path.append("..")

import argparse

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

g_worker_thread = 2
g_engine_thread = 2
g_send_thread = 2
g_outbox_flag = False


def run():
    init_database()

    flow_config = dummy_flow.get_flow_configration()

    import threading
    t = threading.currentThread()
    print('main Thread id : %d  name : %s' % (t.ident, t.getName()))

    worker_list=[]
    for _ in range(g_worker_thread):

        worker = Worker()
        worker_list.append(worker)
        worker.start()


    if g_outbox_flag:
        outbox = OutBox('10.19.17.188', 5673)
        outbox.start()

    engine_list=[]

    for _ in range(g_engine_thread):
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
    for _ in range(g_send_thread):
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

    output_profile(output_path=".", sort_by='cumulative', lines_to_print=30)

    if g_outbox_flag:
        outbox.stop()

    for engine in engine_list:
        engine.stop()

    for worker in worker_list:
        worker.stop()
        worker.join()

    for send_t in send_task_threads:
        send_t.join()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker',default=2)
    parser.add_argument('--engine', default=1)
    parser.add_argument('--send', default=2)
    parser.add_argument('--outbox', default=False)
    parser.add_argument('--interval', default=None)

    args = parser.parse_args()
    print(args)

    global g_worker_thread
    global g_engine_thread
    global g_send_thread
    global g_outbox_flag


    if args.interval:
        sys.setswitchinterval(float(args.interval))

    g_worker_thread = args.worker
    g_engine_thread = args.engine
    g_send_thread = args.send
    g_outbox_flag = args.outbox

    run()

if __name__ == "__main__":
    main()