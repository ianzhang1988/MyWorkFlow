# -*- coding: utf-8 -*-
# @Time    : 2020/10/23 15:47
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import pika
from pika.adapters.utils.connection_workflow import AMQPConnectorException
import json
import threading, traceback, functools, logging, time

from myflow.globalvar import dummy_event_queue
from queue import Empty

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

        self.node_queue_name = 'node_queue'
        self.task_queue_name = 'task_queue'

        self.work_flag = True

        self.work_thread_handle = None

    def connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host, self.port))
        self.node_channel = self.connection.channel()
        self.node_channel.queue_declare(queue=self.node_queue_name, durable=True)
        self.node_channel.basic_qos(prefetch_count=1)
        self.node_channel.confirm_delivery()
        self.task_channel = self.connection.channel()
        self.task_channel.queue_declare(queue=self.task_queue_name, durable=True)
        self.task_channel.confirm_delivery()

    def send_node_event(self, event: dict):

        content = json.dumps(event)
        self.node_channel.basic_publish(
            exchange='',
            routing_key=self.node_queue_name,
            body=content,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))

    def send_task(self, tasks, flow_name = None):
        for t in tasks:
            event = {
                "flow_id": t.flow_id,
                "node_id": t.node_id,
                "task_id": t.id,
            }
            if flow_name:
                event["flow_name"] = flow_name
            self.sent_task_event(event)

    def sent_task_event(self, event: dict):

        content = json.dumps(event)
        self.node_channel.basic_publish(
            exchange='',
            routing_key=self.task_queue_name,
            body=content,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))

    def do_work(self, event, connection, channel, delivery_tag, event_callback):
        try:

            ret = event_callback(event)

            cb = functools.partial(self.on_work_finished, channel, delivery_tag, ret)
            connection.add_callback_threadsafe(cb)

        except Exception as e:
             traceback.print_exc()

    def on_work_finished(self, channel, delivery_tag,  succeeded):

        if channel.is_open:
            # and work_flag:
            # some time when worker has been killed, channel still open,
            # at this time, do not consume the msg unless job is finished
            if self.work_flag or succeeded:
                channel.basic_ack(delivery_tag)

        self.work_thread_handle.join(timeout=3)
        self.work_thread_handle = None

    def on_message(self, event, connection, channel, delivery_tag, event_callback):
        self.work_thread_handle = None
        self.work_thread_handle = threading.Thread(target=self.do_work, args=(event, connection, channel, delivery_tag, event_callback))
        self.work_thread_handle.start()

    def get_node_event(self, event_callback):

        # reconnection loop
        while self.work_flag:
            try:

                self.connect()

                # MQ Main Loop
                for method, properties, body in self.node_channel.consume(self.node_queue_name, inactivity_timeout=1):

                    if not self.work_flag:
                        break

                    if not method:
                        continue

                    event = json.loads(body)

                    self.on_message(event, self.connection, self.node_channel, method.delivery_tag, event_callback)

                    # this simple way block pika ioloop, cause heartbeat timeout then disconnect
                    # worker = TransWorkerHandler()
                    # worker.cmd_handler(job)
                    # cmd_processor.clear_vid()
                    # channel.basic_ack(method.delivery_tag)

            except pika.exceptions.ConnectionClosedByBroker:
                # Uncomment this to make the example not attempt recovery
                # from server-initiated connection closure, including
                # when the node is stopped cleanly
                #
                # break
                continue
                # Do not recover on channel errors
            except pika.exceptions.AMQPChannelError as err:
                logging.error("Caught a channel error: {}, stopping...".format(err))
                break
                # Recover on all other connection errors
            except pika.exceptions.AMQPConnectionError:
                logging.warning("Connection was closed, retrying...")
                continue
            except AMQPConnectorException as e:
                logging.warning("Connector error , retrying...: %s", str(e))
                continue
            finally:
                if self.work_flag:
                    time.sleep(3)

    def stop(self):
        self.work_flag = False

    def start_dummy_event(self):
        t = threading.Thread(target=self._dummy_send_node_event)
        t.daemon = True
        t.start()

    def _dummy_send_node_event(self):
        while self.work_flag:
            try:
                event = dummy_event_queue.get(timeout=1)
                cb = functools.partial(self.send_node_event, event)
                self.connection.add_callback_threadsafe(cb)
            except Empty:
                continue
