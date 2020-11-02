# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 16:24
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import traceback
import threading
from datetime import datetime

from myflow.flowengine.consts import State, EventType
from myflow.flowengine.dao import DatabaseFacade
from myflow.flowengine.event_utlity import EventFacade

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
        flow_config = self.flow_config[flow_name]

        node_id = event['node_id']
        node = self.database_facade.node_state_from_database(flow_config, node_id)

        # check node state， todo: maybe put this inside database_facade
        ready = True
        for n in node.input_nodes:
            if n.state != State.SUCCESS:
                ready = False
                break

        if not ready:
            return None

        # node = self.database_facade.node_from_database(node_id)
        data = node.work()

        node.state = State.SUCCESS
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

        self.database_facade.commit()

    def _process_task(self, event):
        pass

    def create_flow(self, data):
        pass

    def one_step(self, node_event):
        try:
            # get node from database
            event_type = node_event['type']
            node_id = node_event['node_id']

            func = self.process_routine[event_type]
            func(node_event)

        # check event state and data base stated

        # save node to data base and send event to next node
        # so here we need put seeding event in transaction


        # if node type is end, save data and go next loop
        except Exception as e:
            self.database_facade.rollback()
            traceback.print_exc()
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



