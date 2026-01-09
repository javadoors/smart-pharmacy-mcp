from typing import Callable, Dict
from .audit import audit_log

TOOLS: Dict[str, Callable] = {}

def register_tool(name: str, fn: Callable):
    TOOLS[name] = fn

def call_tool(name: str, *args, **kwargs):
    res = TOOLS[name](*args, **kwargs)
    audit_log(name, args, kwargs, res)
    return res