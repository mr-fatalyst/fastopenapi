from typing import Any

from pydantic_core import to_json


def json_encode(data: Any) -> str:
    """Encode data to JSON with safe escaping"""
    return to_json(data).decode("utf-8").replace("</", "<\\/")
