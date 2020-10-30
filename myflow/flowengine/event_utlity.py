# -*- coding: utf-8 -*-
# @Time    : 2020/10/23 15:47
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import pika

# def make_node_event():
#     event = {
#         "type":,
#         "node_num":,
#         "node_id":,
#         "type":,
#         "type":,
#     }
#
#
#     return event

class EventFacade:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.connection = None
        self.node_channel = None
        self.task_channel = None

    def connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host, self.port))
        self.node_channel = self.connection.channel()
        self.node_channel.queue_declare(queue='node_queue', durable=True)


    def send_node_event(self, event):

        pass

    def sent_task_event(self):
        pass

