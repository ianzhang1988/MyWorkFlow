# -*- coding: utf-8 -*-
# @Time    : 2020/10/23 15:47
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import pika
from pika.adapters.utils.connection_workflow import AMQPConnectorException
import json
import threading, traceback, functools, logging, time
from sqlalchemy.exc import OperationalError

from myflow.globalvar import dummy_event_queue
from queue import Empty

from myflow.globalvar import db_session_maker
#from myflow.flowengine.dao import Event
import myflow.flowengine.dao as dao

def make_node_event(flow_name, flow_id, node_id):
    event = {
        "flow_name": flow_name,
        "flow_id": flow_id,
        "node_id": node_id,
    }

    return json.dumps(event)

def make_task_event(flow_id, node_id, task_id, task_num, flow_name=None):
    event = {
        "flow_id": flow_id,
        "node_id": node_id,
        "task_id": task_id,
        "task_num": task_num,
    }

    if flow_name:
        event["flow_name"] = flow_name

    return json.dumps(event)

class OutBox:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.thread = None
        self.work_flag = True
        self.db_session = None
        self.connection = None
        self.node_queue_name = 'node_queue'
        self.task_queue_name = 'task_queue'

    def stop(self):
        self.work_flag = False
        self.thread.join()

    def start(self):
        self.thread = threading.Thread(target=self._work_loop)
        self.thread.start()

    def _connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host, self.port))
        self.node_channel = self.connection.channel()
        self.node_channel.queue_declare(queue=self.node_queue_name, durable=True)
        self.node_channel.confirm_delivery()
        self.task_channel = self.connection.channel()
        self.task_channel.queue_declare(queue=self.task_queue_name, durable=True)
        self.task_channel.confirm_delivery()

    def _work_loop(self):
        while self.work_flag:
            try:
                self.db_session = db_session_maker()
                self._connect()
                self._work()
                self.db_session.close()

            except pika.exceptions.ConnectionClosedByBroker:
                # Uncomment this to make the example not attempt recovery
                # from server-initiated connection closure, including
                # when the node is stopped cleanly
                #
                # break
                logging.warning("Connection was closed by broker, retrying...")
                continue
                # Do not recover on channel errors
            except pika.exceptions.AMQPChannelError as err:
                logging.error("Caught a channel error: {}, stopping...".format(err))
                break
                # Recover on all other connection errors
            except pika.exceptions.AMQPConnectionError:
                traceback.print_exc()
                logging.warning("Connection was closed, retrying...")
                continue
            except AMQPConnectorException as e:
                logging.warning("Connector error , retrying...: %s", str(e))
                continue
            except Exception as e:
                self.db_session.rollback()
                print("@@@@@@ ", e)
                logging.error("OutBox error: %s", e)
                break


    def _work(self):
        while self.work_flag:
            events = None
            try:
                # send_evnet_count = self.db_session.query(dao.Event).filter(dao.Event.is_sent == False).count()
                events = self.db_session.query(dao.Event).filter(dao.Event.is_sent == False).limit(100)\
                    .populate_existing().with_for_update(nowait=True,skip_locked=True).all()
                self.db_session.commit() # don't hold the lock any longer than needed
            except OperationalError as e:
                # other have lock
                time.sleep(0.1)
                continue

            if not events:
                # no event in db
                time.sleep(0.1)
                continue

            #try:
            for e in events:
                # event_db = json.loads(e.data)

                if e.type == "node":
                    #event_mq = make_node_event(event_db["flow_name"], event_db["flow_id"], event_db["node_id"])
                    self.node_channel.basic_publish(
                        exchange='',
                        routing_key=self.node_queue_name,
                        body=e.data,
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                        ))
                elif e.type == "task":
                    #event_mq = make_task_event( event_db["flow_id"], event_db["node_id"], event_db["task_id"], event_db["task_num"])
                    self.task_channel.basic_publish(
                        exchange='',
                        routing_key=self.task_queue_name,
                        body=e.data,
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                        ))
                else:
                    logging.warning("event type not expected: %s", e.type)
                    continue
                e.is_sent = True

            self.db_session.commit()
            # except Exception as e:
            #     print("@@@@@@ ", e)
            #     traceback.print_exc()



class EventFacade:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.connection = None
        self.node_channel = None
        self.node_send_channel = None
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
        # 貌似，用相同的node channel 发送node 事件，会造成读取node事件的时候同时读取多个，引起数据库的问题（一个数据库连接，给多个线程使用）
        # 2020-11-13： 可能不是这样，现在的现象和上面的描述不太一致
        self.node_send_channel = self.connection.channel()
        self.node_send_channel.confirm_delivery()
        self.task_channel = self.connection.channel()
        self.task_channel.queue_declare(queue=self.task_queue_name, durable=True)
        self.task_channel.confirm_delivery()

    # def send_node_event(self, event: dict):
    #
    #     content = json.dumps(event)
    #     self.node_send_channel.basic_publish(
    #         exchange='',
    #         routing_key=self.node_queue_name,
    #         body=content,
    #         properties=pika.BasicProperties(
    #             delivery_mode=2,  # make message persistent
    #         ))

    def send_node_event(self, event: dict):

        def helper():
            content = json.dumps(event)
            self.node_send_channel.basic_publish(
                exchange='',
                routing_key=self.node_queue_name,
                body=content,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))

        self.connection.add_callback_threadsafe(helper)

    def send_task(self, tasks, flow_name = None):
        for t in tasks:
            event = {
                "flow_id": t.flow_id,
                "node_id": t.node_id,
                "task_id": t.id,
                "task_num": t.task_num,
            }
            if flow_name:
                event["flow_name"] = flow_name
            self.sent_task_event(event)

    # def sent_task_event(self, event: dict):
    #
    #     content = json.dumps(event)
    #     self.task_channel.basic_publish(
    #         exchange='',
    #         routing_key=self.task_queue_name,
    #         body=content,
    #         properties=pika.BasicProperties(
    #             delivery_mode=2,  # make message persistent
    #         ))

    def sent_task_event(self, event: dict):

        def helper():
            content = json.dumps(event)
            self.task_channel.basic_publish(
                exchange='',
                routing_key=self.task_queue_name,
                body=content,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))

        self.connection.add_callback_threadsafe(helper)

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
                print("+++++")

                # MQ Main Loop
                for method, properties, body in self.node_channel.consume(self.node_queue_name, inactivity_timeout=1):

                    self.connection.process_data_events()

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
                traceback.print_exc()
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
        time.sleep(2)
        while self.work_flag:
            try:
                event = dummy_event_queue.get(timeout=1)
                cb = functools.partial(self.send_node_event, event)
                self.connection.add_callback_threadsafe(cb)
            except Empty:
                continue
