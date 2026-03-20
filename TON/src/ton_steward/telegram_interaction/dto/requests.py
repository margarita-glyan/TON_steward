from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProcessUpdateRequest:
    raw_update: dict[str, Any]

