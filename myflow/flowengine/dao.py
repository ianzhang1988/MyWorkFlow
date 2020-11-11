# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 17:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
import json


from myflow.globalvar import db_session_maker, db_engine
from datetime import datetime

from myflow.flowengine.flow import FlowConfigration
from myflow.flowengine.node import Task as TaskMem
from myflow.flowengine.consts import State, TaskState

Base = declarative_base()

# class FlowDescDao(Base):
#     __tablename__ = "flow_description"
#     id = Column(Integer, primary_key=True)
#     name = Column(String(256),index=True)
#     description = Column(String(2**16))
#     create_date = Column(DateTime(), index=True)

def to_string(data):
    if isinstance(data, dict):
        return json.dumps(data)
    return str(data)


class Flow(Base):
    __tablename__ = "flow"

    id = Column(Integer,primary_key=True)
    job_id = Column(String(256), index=True)  # who create the flow

    name = Column(String(256),index=True)
    input_data = Column(String(2 ** 24))
    work_data = Column(String(2**24))
    user_data = Column(String(2 ** 24))
    create_date = Column(DateTime(),index=True)
    finish_date = Column(DateTime())
    state = Column(String(256))

    nodes = relationship("Node", backref="user")

    def __repr__(self):
        return "id:{} name:{} state:{} work_data:{} :create_date{}".format(self.id,self.name, self.state, self.work_data, self.create_date)

class FlowDao:
    def __init__(self, flow:FlowConfigration, session_maker):
        self.flow = flow
        self.session_maker = session_maker

    def create(self):
        # save flow to database
        key_nums = sorted(list(self.flow.nodes.keys()))

        # transaction

        session = self.session_maker()

        flow = Flow(name=self.flow.name,
                     input_data=to_string(self.flow.input_data),
                     create_date=datetime.now(),
                     state=self.flow.state)

        session.add(flow)

        for n in key_nums:

            _node = self.flow.nodes[n]

            node = Node(node_num=_node.node_num,
                        input_nodes= _node.input_node_string(),
                        output_nodes= _node.output_node_string(),
                        state = _node.state,
                        create_date = datetime.now())

            flow.nodes.append(node)

        session.commit()

        start_node_id = flow.nodes[0].id

        return flow.id, start_node_id

class Node(Base):
    __tablename__ = "node"

    id = Column(Integer, primary_key=True)
    node_num = Column(Integer)
    flow_id = Column(Integer, ForeignKey("flow.id"))

    input_nodes = Column(String(2**16))
    output_nodes = Column(String(2**16))
    state = Column(String(256))
    work_data = Column(String(2 ** 24))
    user_data = Column(String(2 ** 24))
    create_date = Column(DateTime())
    finish_date = Column(DateTime())

    tasks = relationship("Task", backref="user")

    def __repr__(self):
        return "id:{} node_num:{} flow_id:{} state:{} input_nodes:{} output_nodes:{}".format(
            self.id,self.node_num, self.flow_id, self.state, self.input_nodes, self.output_nodes)

class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("node.id"))
    flow_id = Column(Integer) #,ForeignKey("flow.id")

    task_num = Column(Integer)
    state = Column(String(256))

    input_data = Column(String(2 ** 24))
    work_data = Column(String(2 ** 24))
    user_data = Column(String(2 ** 24))
    create_date = Column(DateTime())
    finish_date = Column(DateTime())

class DatabaseFacade:
    def __init__(self):
        self.session = None

    def init_session(self):
        self.session = db_session_maker()

    def node_state_from_database(self, flow_config , node_id):
        # let keep it simple for now
        return self.node_from_database(flow_config, node_id)

    def _set_ioput_node(self, flow_config, nodes_num_str, node, node_mem_nodes):
        node_num = []
        if "," not in nodes_num_str:
            node_num.append(nodes_num_str)
        else:
            node_num = nodes_num_str.split(",")

        if node_num:
            input_nodes = self.session.query(Node).filter(Node.flow_id==node.flow_id).filter(
                Node.node_num.in_(node_num))
            for n in input_nodes:
                node_mem = flow_config.new_node(n.node_num)
                node_mem.state = n.state
                node_mem.id = n.id
                node_mem.flow_id = n.flow_id
                if n.work_data:
                    node_mem.work_data = json.loads(n.work_data)
                if n.user_data:
                    node_mem.user_data = json.loads(n.user_data)

                node_mem_nodes.append(node_mem)

    def load_tasks(self, node):
        tasks = self.session.query(Task).filter_by(node_id = node.id).all()
        if not tasks:
            return

        for db_task in tasks:

            t = TaskMem()
            t.id = db_task.id
            t.node_id = db_task.node_id
            t.flow_id = db_task.flow_id

            t.task_num = db_task.task_num
            t.state = db_task.state

            # t.input_data = None
            t.work_data = db_task.work_data
            t.user_data = db_task.user_data

            # t.create_date = None
            # t.finish_date = None
            node.add_task(t.task_num, t)

    def node_from_database(self, flow_config, node_id):

        node = self.session.query(Node).filter_by(id=node_id).one()
        print('------ dao.py node_from_database ', node)

        node_mem = flow_config.new_node(node.node_num)
        node_mem.state = node.state
        node_mem.id = node.id
        node_mem.flow_id = node.flow_id

        input_nodes_num_str = node.input_nodes
        output_nodes_num_str = node.output_nodes

        self._set_ioput_node(flow_config, input_nodes_num_str, node, node_mem.input_nodes)
        self._set_ioput_node(flow_config, output_nodes_num_str, node, node_mem.output_nodes)

        # if flow_config.is_task_node(node.node_num):
        #     self.load_tasks(node)

        return node_mem

    def update_node_database(self, node):
        update = {
            Node.state: node.state,
        }

        if node.work_data:
            update[Node.work_data] = to_string(node.work_data)

        if node.user_data:
            update[Node.user_data] = to_string(node.user_data)

        if node.finish_date:
            update[Node.finish_date] = node.finish_date

        self.session.query(Node).filter_by(id=node.id).update(update)

    def update_flow_database(self, flow):
        update = {
            Flow.finish_date: flow.finish_date,
            Flow.state: flow.state
        }

        if flow.work_data:
            update[Flow.work_data] = to_string(flow.work_data)
        if flow.user_data:
            update[Flow.user_data] = to_string(flow.user_data)

        self.session.query(Flow).filter_by(id=flow.id).update(update)

    def get_input_data(self, flow_id):
        input_data = self.session.query(Flow.input_data).filter_by(id=flow_id).one()[0]
        return json.loads(input_data)

    def check_if_flow_state_valid(self, flow_id):
        flow_db = self.session.query(Flow).filter_by(id=flow_id).one()
        return flow_db.state not in (State.SUCCESS, State.FAILED, State.KILLED)

    def check_task_state(self, node_id):

        task_state = TaskState.Waiting

        all_state = self.session.query(Task.state).filter(Task.node_id==node_id).all()

        for (state,) in all_state:
            if state == state.FAILED:
                task_state = TaskState.Error
                break
            if state == state.KILLED:
                task_state = TaskState.Killed
                break

        if all(map(lambda x:x==State.SUCCESS, all_state)):
            task_state = TaskState.Finished

        return task_state

    def add_task(self, tasks):
        for t in tasks:
            t_db = Task(
                node_id = t.node_id,
                flow_id = t.flow_id,
                task_num = t.task_num,
                input_data = to_string(t.input_data),
                create_date = t.create_date,
            )

            self.session.add(t_db)

    def update_failed(self, error, flow_id, node_id=None, task_id=None):
        # if task_id:
        #     self.session.query(Task).filter_by(id=task_id).update({
        #         Task.work_data: to_string(error),
        #         Task.finish_date: datetime.now(),
        #         Task.state: State.FAILED
        #     })

        if node_id:
            self.session.query(Node).filter_by(id=node_id).update({
                Node.work_data: to_string(error),
                Node.finish_date: datetime.now(),
                Node.state: State.FAILED
            })

        self.session.query(Flow).filter_by(id=flow_id).update({
            Flow.work_data: to_string(error),
            Flow.finish_date: datetime.now(),
            Flow.state: State.FAILED
        })

        # self.session.commit()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()



def init_database():
    Base.metadata.create_all(db_engine)

if __name__=="__main__":
    from sqlalchemy import inspect
    from datetime import datetime
    from sqlalchemy.orm import sessionmaker
    from myflow.flowengine.consts import State
    from sqlalchemy import create_engine

    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)

    # for c in list(inspect(FlowDao).columns):
    #     print(c)

    Session = sessionmaker(bind=engine)
    session = Session()

    flow = Flow(name="flow1", state=State.PENDING, work_data="test data", create_date=datetime.now())
    session.add(flow)

    node = Node(node_num=1, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)
    node = Node(node_num=2, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)
    node = Node(node_num=3, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)
    node = Node(node_num=4, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)

    flow = Flow(name="flow2", state=State.PENDING, work_data="test data", create_date=datetime.now())
    session.add(flow)

    node = Node(node_num=1, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)
    node = Node(node_num=2, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)
    node = Node(node_num=3, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
    flow.nodes.append(node)
    node = Node(node_num=4, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data=json.dumps({"v1":"test data"}), create_date=datetime.now())
    flow.nodes.append(node)

    session.commit()

    flows = session.query(Flow)
    for f in flows:
        print(f)

    nodes = session.query(Node)
    for n in nodes:
        print(n)


    nodes = session.query(Node).filter(Node.flow_id == 2)
    for n in nodes:
        print(n)

    flow_1 = session.query(Flow).get(1)
    nodes = flow_1.nodes
    for n in nodes:
        print(n)

    # not SELECT just UPDATE
    session.query(Flow).filter_by(id=1).update({Flow.state: State.SUCCESS})
    session.query(Node).filter(Node.flow_id == 2).update({Node.state: State.SUCCESS})
