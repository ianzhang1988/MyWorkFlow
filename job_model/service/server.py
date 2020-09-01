# -*- coding: utf-8 -*-
# @Time    : 2020/8/28 11:47
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com

from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


# class Foo(BaseModel):
#     id :str
#     value :int
#
# @app.post("/test/{id}")
# async def test(foo: Foo):
#     return {foo.id:foo.value}

item_map = {}

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

@app.post("/items/")
async def create_item(item: Item):
    item_map[item.name] = item
    return item

@app.get("/items/{name}")
async def create_item(name):
    item = item_map[name]
    return item

@app.put("/items/{name}")
async def update_item(name: str, item: Item, q: Optional[str] = None):
    item = item_map[name]
    item.update_forward_refs(**item.dict()) # not work, maybe some other func
    if q:
        item.description += q
    return item

@app.get("/echo_user_agent/")
async def echo_user_agent(user_agent: Optional[str] = Header(None)):
    return {"User-Agent": user_agent}

def get_app():
    return app