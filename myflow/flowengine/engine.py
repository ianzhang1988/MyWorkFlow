# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 16:24
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import traceback
import threading
from datetime import datetime

from myflow.flowengine.consts import State, EventType, FlowError
from myflow.flowengine.dao import DatabaseFacade
from myflow.flowengine.event_utlity import EventFacade
from myflow.flowengine.node import End

class Engine:
    def __init__(self, database_facade : DatabaseFacade, event_facade: EventFacade):
        self.database_facade = database_facade
        self.event_facade = event_facade
        self.work_thread = None

        self.flow_config = {} # name: flow obj

        self.process_routine = {
            'node': self._process_node,
            'task': self._process_task,
        }

    def register_flow(self,name, flow):
        self.flow_config[name] = flow

    def _process_node(self, event):
        flow_name = event['flow_name']
        flow_id = event['flow_id']
        flow_config = self.flow_config[flow_name]

        node_id = event['node_id']
        node = self.database_facade.node_state_from_database(flow_config, node_id)

        # check node state
        if node.state in (State.SUCCESS, State.FAILED, State.KILLED):
            return

        # start node
        if not node.input_nodes:
            node.set_input_data(self.database_facade.get_input_data(flow_id))

        # check input node state， todo: maybe put this inside database_facade
        if node.state == State.PENDING:
            ready = True
            for n in node.input_nodes:
                if n.state != State.SUCCESS:
                    ready = False
                    break

            if not ready:
                return

        # node = self.database_facade.node_from_database(node_id)
        data = node._work()

        node.finish_date = datetime.now()
        self.database_facade.update_node_database(node)

        for n in node.output_nodes:

            event = {
                "flow_name": flow_name,
                "type": EventType.NODE,
                "flow_id": n.flow_id,
                "node_id": n.id,
            }

            # send envet to next node
            self.event_facade.send_node_event(event)


        # if isinstance(node, End):
        #     print('--- end node')

        # end node
        if not node.output_nodes:
            flow = flow_config.new()
            flow.id = flow_id
            flow.work_data = data
            flow.finish_date = datetime.now()
            flow.state = State.SUCCESS

            # update flow in db
            self.database_facade.update_flow_database(flow)

        self.database_facade.commit()

    def _process_node2(self, event):
        flow_name = event['flow_name']
        flow_id = event['flow_id']
        flow_config = self.flow_config[flow_name]

        node_id = event['node_id']
        task_id = event.get('task_id', None)


        node = self.database_facade.node_state_from_database(flow_config, node_id)

        # check node state
        if node.state in (State.SUCCESS, State.FAILED, State.KILLED):
            return

        # start node
        if not node.input_nodes:
            node.set_input_data(self.database_facade.get_input_data(flow_id))

        # check input node state， todo: maybe put this inside database_facade
        if node.state == State.PENDING:
            ready = True
            for n in node.input_nodes:
                if n.state != State.SUCCESS:
                    ready = False
                    break

            if not ready:
                return

        # node = self.database_facade.node_from_database(node_id)

        if flow_config.is_task_node(node.node_num):

            node.reg_check_tasks_state_call( lambda : self.database_facade.check_if_task_in_node_finish(node.id))
            node.reg_get_tasks_call(lambda : self.database_facade.load_tasks(node))
            data = node._work() # should commit before node._work()
            tasks = node.task_for_send()
            if tasks:
                self.database_facade.add_task(tasks)
                self.event_facade.send_task(tasks)
        else:
            data = node._work()

        if node.state == State.SUCCESS:

            node.finish_date = datetime.now()
            self.database_facade.update_node_database(node)

            for n in node.output_nodes:

                event = {
                    "flow_name": flow_name,
                    "type": EventType.NODE,
                    "flow_id": n.flow_id,
                    "node_id": n.id,
                }

                # send envet to next node
                self.event_facade.send_node_event(event)


            # if isinstance(node, End):
            #     print('--- end node')

            # end node
            if not node.output_nodes:
                flow = flow_config.new()
                flow.id = flow_id
                flow.work_data = data
                flow.finish_date = datetime.now()
                flow.state = State.SUCCESS

                # update flow in db
                self.database_facade.update_flow_database(flow)

        self.database_facade.commit()

    def _process_task(self, event):
        pass

    def create_flow(self, data):
        pass

    def _error(self, e, node_event):
        self.database_facade.rollback()

        if node_event['type'] == "node":
            self.database_facade.update_failed(str(e), node_event['flow_id'], node_event['node_id'])
        if node_event['type'] == "task":
            self.database_facade.update_failed(str(e), node_event['flow_id'], node_event['node_id'],
                                               node_event['task_id'])
        self.database_facade.commit()

    def one_step(self, node_event):
        try:
            # get node from database
            event_type = node_event['type']
            flow_id = node_event['flow_id']

            if not self.database_facade.check_if_flow_state_valid(flow_id):
                return True # just consume outdated msg

            # func = self.process_routine[event_type]
            # func(node_event)

            self._process_node2(node_event)

        except FlowError as e:
            self._error(e, node_event)
        except Exception as e:
            self._error(e, node_event)

            traceback.print_exc()

            # sleep ? if there is some bug, sleep can slow down msg from "error retry loop"

            return False

        return True

    def run(self, thread_local_callback):
        self.work_thread = threading.Thread(target=self._run, args=(thread_local_callback,))
        self.work_thread.start()

    def stop(self):
        self.event_facade.stop()
        self.work_thread.join()

    def _run(self, thread_local_callback):
        thread_local_callback()
        self.event_facade.get_node_event(self.one_step)


if __name__ == '__main__':

    from myflow.flowengine.dao import DatabaseFacade
    from .dao import init_database
    init_database()

    database_facade = DatabaseFacade()
    engine = Engine(database_facade)

    engine.create_flow({})



