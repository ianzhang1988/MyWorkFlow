# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 17:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from myflow.globalvar import db_session_maker, db_engine
from datetime import datetime

from myflow.flowengine.flow import FlowConfigration, Flow as FlowMem
from myflow.flowengine.node import Node as NodeMem

Base = declarative_base()

# class FlowDescDao(Base):
#     __tablename__ = "flow_description"
#     id = Column(Integer, primary_key=True)
#     name = Column(String(256),index=True)
#     description = Column(String(2**16))
#     create_date = Column(DateTime(), index=True)


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
                     input_data=self.flow.input_data,
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
    create_date = Column(DateTime(), index=True)
    finish_date = Column(DateTime())

    tasks = relationship("Task", backref="user")

    def __repr__(self):
        return "id:{} node_num:{} flow_id:{} state:{} input_nodes:{} output_nodes:{}".format(
            self.id,self.node_num, self.flow_id, self.state, self.input_nodes, self.output_nodes)

class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("node.id"))
    # flow_id = Column(Integer, ForeignKey("flow.id"))

    work_data = Column(String(2 ** 24))
    user_data = Column(String(2 ** 24))
    create_date = Column(DateTime(), index=True)
    finish_date = Column(DateTime())

class DatabaseFacade:
    def __init__(self):
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
                node_mem.work_data = n.work_data
                node_mem.user_data = n.user_data

                node_mem_nodes.append(node_mem)

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

        # self.session.commit()

        return node_mem

    def update_node_database(self, node):
        node_db = self.session.query(Node).filter_by(id=node.id).one()
        node_db.state = node.state
        node_db.work_data = node.work_data
        node_db.user_data = node.user_data
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
    node = Node(node_num=4, input_nodes="1,2", output_nodes="3,4", state=State.PENDING, work_data="test data", create_date=datetime.now())
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