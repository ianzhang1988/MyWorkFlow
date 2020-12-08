# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 16:24
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import traceback
import threading
from datetime import datetime
import logging
import time

from myflow.flowengine.consts import State, EventType, FlowError
from myflow.flowengine.dao import DatabaseFacade
from myflow.flowengine.event_utlity import EventFacade
from myflow.flowengine.node import End

from myflow.Utility.myprofiler import profile, profile2

class Engine:
    def __init__(self, database_facade : DatabaseFacade, event_facade: EventFacade):
        self.database_facade = database_facade
        self.event_facade = event_facade
        self.work_thread = None

        self.flow_config = {} # name: flow obj

    def register_flow(self,name, flow):
        self.flow_config[name] = flow

    def _process_node(self, event):
        # t = threading.currentThread()
        # print('_process_node Thread id : %d  name : %s' % (t.ident,t.getName()))
        logging.debug("process node event %s", event)


        tasks = None
        flow_name = event['flow_name']
        flow_id = event['flow_id']
        flow_config = self.flow_config[flow_name]
        node_id = event['node_id']

        begin = time.time()
        node = self.database_facade.node_state_from_database(flow_config, node_id)
        print("----- get state time:", time.time() - begin)

        # check node state
        if node.state in (State.SUCCESS, State.FAILED, State.KILLED):
            logging.warning("_process_node invalid node state: %s",node.state)
            return

        # check input node state， todo: maybe put this inside database_facade
        if node.state == State.PENDING:
            ready = True
            for n in node.input_nodes:
                if n.state != State.SUCCESS:
                    ready = False
                    break

            if not ready:
                return

        # load node with work_data
        node = self.database_facade.node_from_database(flow_config, node_id)

        # start node
        if not node.input_nodes:
            node.set_input_data(self.database_facade.get_input_data(flow_id))

        if flow_config.is_task_node(node.node_num):

            node.reg_check_tasks_state_call(lambda : self.database_facade.check_task_state(node.id))
            node.reg_get_tasks_call(lambda : self.database_facade.load_tasks(node))
            data = node._work()
            tasks = node.task_for_send()
            if tasks:
                self.database_facade.add_task(tasks, flow_name)
                # self.event_facade.send_task(tasks, flow_name)
        else:
            data = node._work() # just make sure this is short, so we don't have to commit all around


        if node.state == State.SUCCESS:

            node.finish_date = datetime.now()
            self.database_facade.update_node_database(node)

            for n in node.output_nodes:

                # event = {
                #     "flow_name": flow_name,
                #     "type": EventType.NODE,
                #     "flow_id": n.flow_id,
                #     "node_id": n.id,
                # }

                # send envet to next node
                #self.event_facade.send_node_event(event)

                self.database_facade.add_node_event(n, flow_name)


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
        else:
            self.database_facade.update_node_database(node)

        self.database_facade.commit()

        # if tasks:
        #     self.event_facade.send_task(tasks, flow_name)

    def _process_task(self, event):
        pass

    def create_flow(self, data):
        pass

    def _error(self, e, node_event):
        self.database_facade.rollback()

        self.database_facade.update_failed(str(e), node_event['flow_id'], node_event['node_id'])

        self.database_facade.commit()

    # @profile(sort_by='cumulative', lines_to_print=10)
    @profile2("one_step")
    def one_step(self, node_event):

        try:
            begin = time.time()

            t = threading.currentThread()
            print('one_step Thread id : %d  name : %s' % (t.ident, t.getName()))
            print("one_step %s"%node_event)

            logging.info("one_step event %s", node_event)

            self.database_facade.init_session()
            # get node from database
            # event_type = node_event['type']
            flow_id = node_event['flow_id']

            begin2 = time.time()

            if not self.database_facade.check_if_flow_state_valid(flow_id):
                logging.info("one_step invalid state, flow_id %s", flow_id)
                return True # just consume outdated msg

            print("+++++ check state time", time.time() - begin2)

            self._process_node(node_event)

            print("***** one_step time",time.time()-begin)

        except FlowError as e:
            self._error(e, node_event)
            return False
        except Exception as e:
            self._error(e, node_event)

            print("one step Error: %s\n" % traceback.format_exc())

            # sleep ? if there is some bug, sleep can slow down msg from "error retry loop"

            return False
        finally:
            # close session here, or it would be close by other thread, and cause exception
            self.database_facade.release_session()


        return True

    def run(self):
        self.work_thread = threading.Thread(target=self._run)
        self.work_thread.start()

    def stop(self):
        self.event_facade.stop()
        self.work_thread.join()

    def _run(self):
        # t = threading.currentThread()
        # print('init session Thread id : %d  name : %s' % (t.ident,t.getName()))
        self.event_facade.get_node_event(self.one_step)


if __name__ == '__main__':

    from myflow.flowengine.dao import DatabaseFacade
    from .dao import init_database
    init_database()

    database_facade = DatabaseFacade()
    engine = Engine(database_facade)

    engine.create_flow({})



