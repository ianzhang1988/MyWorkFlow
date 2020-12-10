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

    outbox = OutBox('10.19.17.188', 5673)
    outbox.start()

    for _ in range(1000):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            break

    print("timeout stop")

    output_profile(output_path=".", sort_by='cumulative', lines_to_print=30)


    outbox.stop()


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