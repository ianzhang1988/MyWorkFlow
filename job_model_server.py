# -*- coding: utf-8 -*-
# @Time    : 2020/8/28 11:29
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from job_model.service.server import get_app
from job_model.dao.db import init_db

init_db()
app = get_app()

if __name__ == '__main__':
    pass