from typing import Any

from pydantic import BaseModel


class Item(BaseModel):
    name: str
    value: int


def echo_int(x: int):
    return {"x": x}


async def async_echo_int(x: int):
    return {"x": x}


def echo_int_duplicate(x: int):
    return {"x": x}


def return_item_model(item: Item):
    return item


def use_default_param(x: int = 42):
    return {"x": x}


def raise_value_error():
    raise ValueError("Something went wrong")


def echo_both(x: int, item: Item):
    return {"x": x, "item": item}


def echo(x: Any):
    return x
