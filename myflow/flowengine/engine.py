# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 16:24
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import traceback

from myflow.globalvar import node_event_queue
from myflow.flowengine.consts import State, EventType

class Engine:
    def __init__(self, database_facade):
        self.database_facade = database_facade

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
        self.database_facade.update_node_database(node)

        for n in node.output_nodes:

            event = {
                "flow_name": flow_name,
                "type": EventType.NODE,
                "flow_id": n.flow_id,
                "node_id": n.id,
            }

            # send envet to next node
            node_event_queue.put(event)

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


if __name__ == '__main__':

    from myflow.flowengine.dao import DatabaseFacade
    from .dao import init_database
    init_database()

    database_facade = DatabaseFacade()
    engine = Engine(database_facade)

    engine.create_flow({})

    node_event_queue.put(None)

    for _ in range(10):
        event = node_event_queue.pop()
        engine.one_step(event)


