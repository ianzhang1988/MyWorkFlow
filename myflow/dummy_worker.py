# -*- coding: utf-8 -*-
# @Time    : 2020/11/10 16:44
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from myflow.globalvar import db_session_maker
from myflow.flowengine.dao import Task
from myflow.globalvar import dummy_event_queue

import pika
import json

class Worker:
    def __init__(self):
        self.work_flag = True
        self.db_session = db_session_maker()

    def stop(self):
        self.work_flag = False

    def send_event(self, task_event):
        event = {
            "flow_name": task_event["flow_name"],
            "flow_id": task_event["flow_id"],
            "node_id": task_event["node_id"],
            "task_id": task_event["task_id"],
        }

        dummy_event_queue.put(event)


    def run(self):
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

            task_event = json.loads(body)

            task_id = task_event["task_id"]

            task = self.db_session.query(Task).filter(Task.id == task_id)

            input_data = json.loads(task.input_data)

            output_value = input_data["value"]*2

            task.work_data = json.dumps({"value": output_value})

            self.db_session.commit()
            self.send_event(task_event)

            # 上面这个样子，commit后线程挂了，那么就没有事件发送出来，流程就停住了
            # 下面的方式，有个问题，如果消息先被处理了，而commit还没有做完，接收端可能拿不到正确的数据
            #
            # 事务性发件箱模式，看来还是最成熟的方式
            # self.flow_mq_connection.add_callback_threadsafe()
            # self.db_session.commit()

            channel.basic_ack(method.delivery_tag)


