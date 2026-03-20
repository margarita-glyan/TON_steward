from __future__ import annotations

import datetime as dt
from typing import Any


def jsonable(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return value


def pick_dict(obj: Any, fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields:
        out[f] = jsonable(getattr(obj, f))
    return out

