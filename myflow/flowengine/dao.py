# -*- coding: utf-8 -*-
# @Time    : 2020/10/19 17:58
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Text, DateTime


Base = declarative_base()

class FlowDao(Base):
    __tablename__ = "flow"

    id = Column(Integer(),primary_key=True)
    