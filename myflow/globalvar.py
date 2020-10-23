# -*- coding: utf-8 -*-
# @Time    : 2020/10/20 16:27
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from queue import Queue


db_engine = create_engine('sqlite:///:memory:', echo=True)
session_factory = sessionmaker(bind=db_engine)
db_session_maker = scoped_session(session_factory)


def deinit():
    global db_session_maker
    db_session_maker.remove()


task_queue = Queue(10)

node_event_queue = Queue(100)

