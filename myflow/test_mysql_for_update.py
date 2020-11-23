# -*- coding: utf-8 -*-
# @Time    : 2020/11/23 16:51
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import OperationalError

from myflow.flowengine.dao import init_database, Test

init_database()

db_engine1 = create_engine('mysql://root:zhang@10.19.17.188:3307/test', echo=False)
session_factory1 = sessionmaker(bind=db_engine1)

session1 = session_factory1()

try:
    data = session1.query(Test).filter(Test.id > 4).limit(100)\
                    .populate_existing().with_for_update(nowait=True,skip_locked=True).all()


    for d in data:
        print(d)

    print(data)
except OperationalError as e:
    print(e)
    print(dir(e))