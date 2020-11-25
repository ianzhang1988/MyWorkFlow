# -*- coding: utf-8 -*-
# @Time    : 2020/11/10 16:44
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import threading
from threading import Thread
import pika
import json
import logging

from myflow.globalvar import db_session_maker
from myflow.flowengine.consts import State
from myflow.flowengine.dao import Task, Event
from myflow.globalvar import dummy_event_queue
import sqlalchemy
from datetime import datetime


class Worker(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.work_flag = True
        self.db_session = None

    def stop(self):
        self.work_flag = False

    def send_event(self, task_event):
        event = {
            "flow_name": task_event["flow_name"],
            "flow_id": task_event["flow_id"],
            "node_id": task_event["node_id"],
            "task_id": task_event["task_id"],
        }


        # dummy_event_queue.put(event)
        out_box_entry = Event(type="node", data=json.dumps(event), create_date=datetime.now())
        self.db_session.add(out_box_entry)

    def run(self):
        t = threading.currentThread()
        print('dummy worker Thread id : %d  name : %s' % (t.ident, t.getName()))
        self.db_session = db_session_maker()

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='10.19.17.188', port=5673))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)

        channel.basic_qos(prefetch_count=1)

        for method, properties, body in channel.consume('task_queue', inactivity_timeout=1):
            if not self.work_flag:
                break

            if not method:
                continue

            print("+++ dummy worker body %s" % body)
            task_event = json.loads(body)

            task_id = task_event["task_id"]
            node_id = task_event["node_id"]
            # if "task_num" not in task_event:
            #     channel.basic_ack(method.delivery_tag)
            #     continue
            task_num = task_event["task_num"]

            try:
                if task_id:
                    task = self.db_session.query(Task).filter(Task.id == task_id).one()
                else:
                    # print("!!!!!!!!!!",self.db_session.query(Task).filter(Task.node_id == node_id).filter(Task.task_num == task_num))
                    task = self.db_session.query(Task).filter(Task.node_id == node_id).filter(Task.task_num == task_num).first()
            except sqlalchemy.orm.exc.NoResultFound as e:
                print("!!!! data error, continue")
                channel.basic_ack(method.delivery_tag)
                continue

            if not task:
                logging.error("dummy worker task no task found %s", body)
                continue

            task.state = State.WORKING

            input_data = json.loads(task.input_data)

            output_value = input_data["value"]*2

            task.work_data = json.dumps({"value": output_value})
            task.state = State.SUCCESS

            self.db_session.commit()
            self.send_event(task_event)

            # 上面这个样子，commit后线程挂了，那么就没有事件发送出来，流程就停住了
            # 下面的方式，有个问题，如果消息先被处理了，而commit还没有做完，接收端可能拿不到正确的数据
            #
            # 事务性发件箱模式，看来还是最成熟的方式
            # self.flow_mq_connection.add_callback_threadsafe()
            # self.db_session.commit()

            channel.basic_ack(method.delivery_tag)


