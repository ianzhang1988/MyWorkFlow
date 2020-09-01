# -*- coding: utf-8 -*-
# @Time    : 2020/9/1 11:40
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Text, DateTime
from datetime import datetime, timedelta
from sqlalchemy.sql import select


engine = create_engine('mysql://root:zhang@10.19.17.188/test', echo=True)
jobs = None
tasks = None

def init_db():
    metadata = MetaData()

    global jobs, tasks

    jobs = Table('job', metadata,
                 Column('id', String(256), primary_key=True),
                 Column('create_date', DateTime, index=True),
                 Column('work_data', Text(65536)),
                 Column('user_data', Text(65536)),
                 # state
                 )

    tasks = Table('task', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('job_id', None, ForeignKey('job.id')),
                  Column('work_data', Text(65536)),
                  Column('user_data', Text(65536)),
                  )

    metadata.create_all(engine)

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

    s = select([jobs]).where(jobs.c.id == id)
    result = engine.execute(s)
    if result.first() is not None:
        return False

    ins = jobs.insert()
    result = engine.execute(ins, id=id, create_date=datetime.now(), work_data=work_data, user_data=user_data)

    return True

def get_job(id):
    s = select([jobs]).where(jobs.c.id == id)
    result = engine.execute(s)
    return result.first()


if __name__ == '__main__':
    init_db()
    conn = engine.connect()

    add_column(engine, 'job', Column('create_date', DateTime, index=True))
    drop_column(None, 'job', 'profile')

    ins = jobs.insert()
    # conn.execute(ins, [
    #     {'id': '1000', 'work_data': 'some work data 1', 'user_data':''},
    #     {'id': '1001', 'work_data': 'some work data 2', 'user_data': ''},
    #     {'id': '1002', 'work_data': 'some work data 3', 'user_data': ''},
    #     {'id': '1003', 'work_data': 'some work data 4', 'user_data': ''},
    # ])

    today = datetime.now()

    print(tasks.c)

    # conn.execute(ins, [
    #     {'id': '1007', 'create_date': today - timedelta(days=2), 'work_data': 'some work data 7', 'user_data':''},
    #     {'id': '1008', 'create_date': today - timedelta(days=1), 'work_data': 'some work data 8', 'user_data': ''},
    #     {'id': '1009', 'create_date': today , 'work_data': 'some work data 9', 'user_data': ''},
    # ])

    s = select([jobs])
    result = conn.execute(s)
    for row in result:
        print(row)

    s = select([jobs]).where(jobs.c.id == '1000')
    result = conn.execute(s)
    print(result.first())

    s = select([jobs]).where(jobs.c.id == '2000')
    result = conn.execute(s)
    print(result.first())