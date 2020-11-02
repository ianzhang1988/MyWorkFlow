# -*- coding: utf-8 -*-
# @Time    : 2020/10/20 16:27
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

#db_engine = create_engine('sqlite:///:memory:', echo=True)
db_engine = create_engine('sqlite:///D:\\WorkSpace\\mywork\\MyWorkFlow\\myflow\\test.db', echo=False)
session_factory = sessionmaker(bind=db_engine)
db_session_maker = scoped_session(session_factory)

def deinit():
    global db_session_maker
    db_session_maker.remove()
