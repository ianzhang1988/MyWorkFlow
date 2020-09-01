# -*- coding: utf-8 -*-
# @Time    : 2020/8/28 11:28
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from pydantic import BaseModel
from typing import Optional

from .server import get_app
from job_model.dao.db import add_job as add_job_db, get_job as get_job_db

class Job(BaseModel):
    id: str
    work_data: str
    user_data: Optional[str] = None

class Task(BaseModel):
    id: Optional[int] = None
    job_id: str
    work_data: str
    user_data: Optional[str] = None

app = get_app()

@app.post("/job/")
async def add_job(job: Job):
    if add_job_db(job.id, job.work_data, job.user_data):
        return job
    else:
        return {"error": "exists"}

@app.get("/job/{job_id}")
async def get_job(job_id):
    job_db = get_job_db(job_id)
    if job_db is None:
        return {"error":"not found"}

    # job=Job()
    # job.id=job_db.id
    # job.work_data = job_db.work_data
    # if job_db.user_data:
    #     job.user_data = job_db.user_data
    return job_db