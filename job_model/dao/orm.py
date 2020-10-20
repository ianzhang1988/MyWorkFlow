# -*- coding: utf-8 -*-
# @Time    : 2020/9/23 18:46
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

# -*- coding: utf-8 -*-
# @Time    : 2020/9/1 11:40
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Text, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta


engine = create_engine('mysql://root:zhang@10.19.17.188/test', echo=True)
jobs = None
tasks = None

Base = declarative_base()

Session = sessionmaker(bind=engine)

class Job(Base):
    __tablename__ = "job"

    id = Column(String(256), primary_key=True)
    create_date = Column(DateTime, index=True)
    work_data = Column(Text(65536))
    user_data = Column(Text(65536))
    # task_report = Column(Text(16777215))

    def __repr__(self):
        return 'id: %s' % self.id

# class Task(Base):
#     __talbename__ = "task"
#
#     id = Column(Integer, primary_key=True)


def init_db():
    Base.metadata.bind = engine
    Base.metadata.create_all()

def add_column(engine, table_name, column):
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    sql = 'ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type)
    print(sql)
    #engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type))

def drop_column(engine, table_name, column_name):
    sql = 'ALTER TABLE %s DROP COLUMN %s' % (table_name, column_name)
    #engine.execute('ALTER TABLE %s DROP COLUMN %s' % (table_name, column_name))
    print(sql)



def add_job(id, work_data, user_data=''):
    ses = Session()

    result = ses.query(Job).filter(Job.id == id)

    if result.first() is not None:
        return False

    ses.add(Job(id=id, create_date=datetime.now(), work_data=work_data, user_data=user_data))

    ses.commit()
    return True

def get_job(id):
    ses = Session()

    result = ses.query(Job).filter(Job.id == id)
    return result.first()


if __name__ == '__main__':
    init_db()
    conn = engine.connect()

    # add_column(engine, 'job', Column('create_date', DateTime, index=True))
    # drop_column(None, 'job', 'profile')

    # conn.execute(ins, [
    #     {'id': '1000', 'work_data': 'some work data 1', 'user_data':''},
    #     {'id': '1001', 'work_data': 'some work data 2', 'user_data': ''},
    #     {'id': '1002', 'work_data': 'some work data 3', 'user_data': ''},
    #     {'id': '1003', 'work_data': 'some work data 4', 'user_data': ''},
    # ])

    # add_job("3001", "some work data 1", "")
    # add_job("3002", "some work data 2", "")
    # add_job("3003", "some work data 3", "")

    print(get_job('3001'))
    print(get_job('3002'))
    print(get_job('3003'))